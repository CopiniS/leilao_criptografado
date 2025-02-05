import socket
import struct
import threading
from datetime import timedelta
import json
import criptografia
import time

class Server:
    def __init__(self):

        with open('config.json', 'r') as f:
            config = json.load(f)

        with open('dados_server.json', 'r') as f:
            dados_server = json.load(f)

        self.HOST = config['server_ip']
        self.PORT = config['server_main_port']
        self.PORT_LANCES = dados_server['server_lances_port']
        self.HOST_MULTICAST = dados_server['multicast_ip']
        self.PORT_MULTICAST = dados_server['multicast_port']
        self.clients = {}
        self.item_leilao = {}
        self.leilao_ativo = False
        self.multicast_address = None
        self.multicast_socket = None
        self.lock = threading.Lock()

        self.participantes = dados_server['participantes']
        self.chave_simetrica = dados_server['chave_simetrica']


    def cria_multicast(self):
        self.multicast_address = (self.HOST_MULTICAST, self.PORT_MULTICAST)
        self.multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ttl = struct.pack('b', 1)
        self.multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        print(f"Canal multicast criado: {self.HOST_MULTICAST}:{self.PORT_MULTICAST}")

    def publica_item(self, nome: str, lance_inicial: float, step_lances: float, tempo_em_segundos: int):
        self.cria_multicast()

        self.item_leilao = {
            "nome": nome,
            "lance_inicial": lance_inicial,
            "step_lances": step_lances,
            "tempo": timedelta(seconds=tempo_em_segundos),
            "maior_lance": lance_inicial,
            "usuario": None
        }
        self.leilao_ativo = True
        print(f"Item publicado: {self.item_leilao}")

        threading.Thread(target=self.gerencia_tempo).start()
        threading.Thread(target=self.escuta_lances).start()


    def gerencia_tempo(self):
        tempo_restante = self.item_leilao["tempo"]
        while self.leilao_ativo and tempo_restante.total_seconds() > 0:
            self.envia_atualizacao()
            tempo_restante -= timedelta(seconds=1)
            self.item_leilao["tempo"] = tempo_restante
            
            time.sleep(1)  # Garantir que o tempo seja atualizado corretamente

        self.leilao_ativo = False
        self.envia_atualizacao(finalizado=True)
        print("Leilão encerrado.")


    def escuta_lances(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.HOST, self.PORT_LANCES))
        server_socket.listen()
        print(f"Servidor escutando lances em {self.HOST}:{self.PORT}")

        while self.leilao_ativo:
            conn, addr = server_socket.accept()
            print(f"Conectado por {addr}")

            textoCriptografado = conn.recv(1024).decode('utf-8')
            print('texto criptografado em lance: ', textoCriptografado)
            textoClaro = criptografia.descriptografaSimetrica(textoCriptografado, self.chave_simetrica)

            print('textoClaro: ', textoClaro)

            dados_json = json.loads(textoClaro)

            resposta = self.processa_lance(dados_json)
            textoClaro = json.dumps(resposta)
            textoCriptografado = criptografia.criptografaSimetrica(textoClaro, self.chave_simetrica)
            conn.sendall(textoCriptografado.encode('utf-8'))
            print('retorna resposta do lance')
            

    def envia_resposta_unicast(self, resposta, cliente_addr):
        """ Envia uma resposta diretamente para o cliente que enviou o lance (unicast) """
        try:
            envio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

            textoClaro = json.dumps(resposta)
            textoCriptografado = criptografia.criptografaSimetrica(textoClaro, self.chave_simetrica)

            print('envia resposta do lance', textoCriptografado)

            envio_socket.sendto(textoCriptografado.encode('utf-8'), cliente_addr)  # Envia direto para o cliente
            print(f"[SERVIDOR] Resposta enviada para {cliente_addr}: {resposta}")

        except Exception as e:
            print(f"[SERVIDOR] Erro ao enviar resposta para {cliente_addr}: {e}")

        finally:
            envio_socket.close()


    def processa_lance(self, dados_json):
        print('entra em processa lance')
        lance = float(dados_json['lance'])
        cpf = dados_json['cpf_no_lance']
        
        with self.lock:  # Garante que apenas uma thread altere `self.item_leilao`
            if lance < self.item_leilao['maior_lance'] + self.item_leilao['step_lances']:
                return {'sucesso': False, 'erro': '[ERRO]: Lance enviado menor do que o obrigatório', 'data': None}

            self.item_leilao["maior_lance"] = lance
            self.item_leilao["usuario"] = cpf
            print(f"Novo maior lance: {self.item_leilao['maior_lance']} de {self.item_leilao['usuario']}")
        return {'sucesso': True, 'erro': None, 'data': None}

    def envia_atualizacao(self, finalizado=False):
        if not self.multicast_socket or not self.multicast_address:
            print('[ERRO]: Canal multicast nao configurado adequadamente')
            return
        with self.lock:
            status = {
                "produto": self.item_leilao["nome"],
                "maior_lance": self.item_leilao["maior_lance"],
                "tempo": str(self.item_leilao["tempo"]),
                "step_lances": self.item_leilao['step_lances'],
                "finalizado": finalizado
            }

        resposta = {'sucesso': True, 'erro': None, 'data': status}

        textoClaro = json.dumps(resposta)
        textoCriptografado = criptografia.criptografaSimetrica(textoClaro, self.chave_simetrica)

        self.multicast_socket.sendto(textoCriptografado.encode('utf-8'), self.multicast_address)

    def verificacoes_entrada(self, resultado, addr):
        if not self.leilao_ativo:
            return {'sucesso': False, 'erro': 'Nenhum Item está sendo leiloado no momento', 'data': None}

        if not resultado:
            return {'sucesso': False, 'erro': 'CPF não cadastrado', 'data': None}
        return {'sucesso': True, 'erro': None, 'data': {'chave_simetrica': self.chave_simetrica, 'endereco_multicast': self.multicast_address, 'port_lances': self.PORT_LANCES}}


    def handle_client(self, conn, addr):
        try:
            data = conn.recv(1024).decode('utf-8')
            dados_json = json.loads(data)

            if not "cpf" in dados_json: 
                print('[ERRO]: Dados inesperados na requisição')
            else:
                resultado = next((p for p in self.participantes if p["cpf"] == dados_json['cpf']), None)
                
                if resultado is None:
                    resposta = {"erro": "CPF não encontrado"}
                    textoClaro = json.dumps(resposta)
                else:
                    resposta = self.verificacoes_entrada(resultado, addr)
                    textoClaro = json.dumps(resposta)
                    textoCriptografado = criptografia.criptografaAssimetrica(textoClaro, resultado['chave_publica'])

                conn.sendall(textoCriptografado.encode('utf-8') if resultado else textoClaro.encode('utf-8'))

        except json.JSONDecodeError:
            print("[ERRO]: Falha ao decodificar JSON")
        except Exception as e:
            print(f"[ERRO]: {e}")
        finally:
            conn.close()


    def main(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.HOST, self.PORT))
        server_socket.listen()
        print(f"Servidor escutando em {self.HOST}:{self.PORT}")

        while True:
            conn, addr = server_socket.accept()
            print(f"Conectado por {addr}")
            threading.Thread(target=self.handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    server = Server("127.0.0.1", 65432)
    server.main()
