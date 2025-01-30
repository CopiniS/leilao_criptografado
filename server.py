import socket
import struct
import threading
from datetime import timedelta
import json
import criptografia

class Server:
    def __init__(self, host: str, port: int):
        self.HOST = host
        self.PORT = port
        self.clients = {}
        self.item_leilao = {}
        self.leilao_ativo = False
        self.multicast_address = None
        self.multicast_socket = None

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
        self.
        print(f"Item publicado: {self.item_leilao}")

        threading.Thread(target=self.gerencia_tempo).start()
        threading.Thread(target=self.escuta_lances).start()

    def gerencia_tempo(self):
        tempo_restante = self.item_leilao["tempo"]
        while self.leilao_ativo and tempo_restante.total_seconds() > 0:
            print(f"Tempo restante: {tempo_restante}")
            self.envia_atualizacao()
            tempo_restante -= timedelta(seconds=1)
            self.item_leilao["tempo"] = tempo_restante
            threading.Event().wait(1)

        self.leilao_ativo = False
        self.envia_atualizacao(finalizado=True)
        print("Leilão encerrado.")

    def escuta_lances(self):
        if not self.multicast_address:
            print("Canal multicast não configurado.")
            return

        recepcao_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        recepcao_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        recepcao_socket.bind((self.multicast_address[0], self.multicast_address[1]))

        grupo = socket.inet_aton(self.multicast_address[0])
        mreq = struct.pack("4sL", grupo, socket.INADDR_ANY)
        recepcao_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while self.leilao_ativo:
            data, addr = recepcao_socket.recvfrom(1024)
            mensagem = data.decode("utf-8")
            print(f"Mensagem recebida de {addr}: {mensagem}")
            self.processa_lance(mensagem, addr)

    def processa_lance(self, mensagem: str, addr):
        try:
            lance, usuario = mensagem.split(":")
            lance = float(lance)
            
            if lance > self.item_leilao["maior_lance"]:
                self.item_leilao["maior_lance"] = lance
                self.item_leilao["usuario"] = usuario
                print(f"Novo maior lance: {lance} de {usuario}")
                self.envia_atualizacao()
            else:
                print(f"Lance rejeitado: {lance} é menor ou igual ao maior lance atual.")
        except ValueError:
            print(f"Formato de mensagem inválido: {mensagem}")

    def envia_atualizacao(self, finalizado=False):
        resposta = {}

        if not self.multicast_socket or not self.multicast_address:
            resposta {'sucesso': False, 'erro': 'Canal multicast não configurado para envio', 'data': None}

        else:
            with open('participantes.json', 'r', encoding='utf-8') as file:
            chave_simetrica = json.load(file)['chave_simetrica']

            status = {
                "produto": self.item_leilao["nome"],
                "maior_lance": self.item_leilao["maior_lance"],
                "tempo": str(self.item_leilao["tempo"]),
                "step_lances": self.item_leilao['step_lances']
                "finalizado": finalizado
            }

            resposta = {'sucesso': True, 'erro': None, 'data': status}

        textoClaro = json.dumps(resposta)
        textoCriptografado = criptografia.criptografaSimetrica(textoClaro, chave_simetrica)

        self.multicast_socket.sendto(textoCriptografado.encode('utf-8'), self.multicast_address)

    def handle_client(self, conn, addr):
        data = conn.recv(1024).decode('utf-8')
        resposta = {}
        if not self.leilao_ativo:
            resposta {'sucesso': False, 'erro': 'Nenhum Item está sendo leiloado no momento', 'data': None}

        dados_json = json.loads(data) 

        with open('participantes.json', 'r', encoding='utf-8') as file:
            participantes = json.load(file)['participantes']
            chave_simetrica = json.load(file)['chave_simetrica']

        resultado = next((participante for participante in participantes if participante["cpf"] == dados_json['cpf']), None)

        if not resultado:
            resposta = {'sucesso': False, 'erro': 'CPF não cadastrado', 'data': None}

        else:
            resposta = {'sucesso': True, 'erro': None, 'data': {'chave_simetrica': chave_simetrica, 'endereco_multicast': self.multicast_address}}

        textoClaro = json.dumps(resposta)
        textoCriptografado = criptografia.criptografaAssimetrica(textoClaro, resultado['chave_publica'])
        conn.sendall(textoCriptografado.encode('utf-8'))

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
