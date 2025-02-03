import socket
import struct
import threading
from datetime import timedelta
import json
import criptografia
import time

class Server:
    def __init__(self, host: str, port: int):
        self.HOST = host
        self.PORT = port
        self.clients = {}
        self.item_leilao = {}
        self.leilao_ativo = False
        self.multicast_address = None
        self.multicast_socket = None
        self.lock = threading.Lock()

        with open('dados_publicos.json', 'r', encoding='utf-8') as file:
            json_data = json.load(file)
            self.participantes = json_data['participantes']
            self.chave_simetrica = json_data['chave_simetrica']


    def cria_multicast(self, grupo_multicast="224.0.0.1", porta_multicast=5007):
        self.multicast_address = (grupo_multicast, porta_multicast)
        self.multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ttl = struct.pack('b', 1)
        self.multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        print(f"Canal multicast criado: {grupo_multicast}:{porta_multicast}")

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
        # threading.Thread(target=self.escuta_lances).start()


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


    # def escuta_lances(self):
    #     if not self.multicast_address:
    #         print("Canal multicast não configurado.")
    #         return

    #     recepcao_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #     recepcao_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #     recepcao_socket.bind(('0.0.0.0', self.multicast_address[1]))

    #     grupo = socket.inet_aton(self.multicast_address[0])
    #     mreq = struct.pack("4sL", grupo, socket.INADDR_ANY)
    #     recepcao_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    #     while self.leilao_ativo:
    #         data, addr = recepcao_socket.recvfrom(1024)
    #         textoCriptografado = data.decode("utf-8")
    #         textoClaro = criptografia.descriptografaSimetrica(textoCriptografado, self.chave_simetrica)
    #         dados_json = json.loads(textoClaro)
    #         print('recebido lance: ', dados_json)
    #         resposta = self.processa_lance(dados_json, addr)
    #         self.envia_resposta_unicast(resposta, addr)

    #         # Envia resposta apenas para o remetente do lance
    #         recepcao_socket.sendto(textoCriptografado.encode("utf-8"), addr)

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
        return {'sucesso': True, 'erro': None, 'data': {'chave_simetrica': self.chave_simetrica, 'endereco_multicast': self.multicast_address}}


    def handle_client(self, conn, addr):
        try:
            data = conn.recv(1024).decode('utf-8')
            print('recebe unicast: ', data)

            dados_json = json.loads(data)

            if "cpf" in dados_json: 
                print('entra em cpf')
                resultado = next((p for p in self.participantes if p["cpf"] == dados_json['cpf']), None)
                
                if resultado is None:
                    resposta = {"erro": "CPF não encontrado"}
                    textoClaro = json.dumps(resposta)
                else:
                    resposta = self.verificacoes_entrada(resultado, addr)
                    textoClaro = json.dumps(resposta)
                    textoCriptografado = criptografia.criptografaAssimetrica(textoClaro, resultado['chave_publica'])

                conn.sendall(textoCriptografado.encode('utf-8') if resultado else textoClaro.encode('utf-8'))

            elif "lance" in dados_json:
                print('entra aqui em lance')
                resposta = self.processa_lance(dados_json)
                textoClaro = json.dumps(resposta)
                textoCriptografado = criptografia.criptografaSimetrica(textoClaro, self.chave_simetrica)
                conn.sendall(textoCriptografado.encode('utf-8'))
                print('retorna resposta do lance')

            else:
                print('[MENSAGEM INESPERADA]: a mensagem não continha as informações esperadas')

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
