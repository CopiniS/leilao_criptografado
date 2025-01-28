import socket
import struct
import threading
from datetime import timedelta, datetime
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import os

class Server:
    def __init__(self, host: str, port: int):
        self.HOST = host
        self.PORT = port
        self.clients = {}
        self.item_leilao = None
        self.leilao_ativo = False
        self.chave_simetrica = os.urandom(32)  # Chave AES de 256 bits
        self.multicast_address = None
        self.multicast_socket = None

    def cria_multicast(self, grupo_multicast="224.0.0.1", porta_multicast=5007):
        self.multicast_address = (grupo_multicast, porta_multicast)
        self.multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ttl = struct.pack('b', 1)
        self.multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        print(f"Canal multicast criado: {grupo_multicast}:{porta_multicast}")

    def publica_item(self, nome: str, lance_inicial: float, step_lances: float, tempo_em_segundos: int):
        # Criar canal multicast ao publicar o produto
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

        # Iniciar threads para gerenciar tempo e escutar lances
        threading.Thread(target=self.gerencia_tempo).start()
        threading.Thread(target=self.escuta_lances).start()

    def gerencia_tempo(self):
        tempo_restante = self.item_leilao["tempo"]
        while self.leilao_ativo and tempo_restante.total_seconds() > 0:
            print(f"Tempo restante: {tempo_restante}")
            self.envia_atualizacao()
            tempo_restante -= timedelta(seconds=1)
            self.item_leilao["tempo"] = tempo_restante
            threading.Event().wait(1)  # Espera de 1 segundo

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
        if not self.multicast_socket or not self.multicast_address:
            print("Canal multicast não configurado para envio.")
            return

        status = {
            "nome": self.item_leilao["nome"],
            "maior_lance": self.item_leilao["maior_lance"],
            "usuario": self.item_leilao["usuario"],
            "tempo_restante": str(self.item_leilao["tempo"]),
            "finalizado": finalizado
        }
        mensagem = str(status).encode("utf-8")
        self.multicast_socket.sendto(mensagem, self.multicast_address)

    def main(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.HOST, self.PORT))
        server_socket.listen()
        print(f"Servidor escutando em {self.HOST}:{self.PORT}")

        while True:
            conn, addr = server_socket.accept()
            print(f"Conectado por {addr}")
            threading.Thread(target=self.handle_client, args=(conn, addr)).start()

    def handle_client(self, conn, addr):
        data = conn.recv(1024)
        print(f"Mensagem recebida: {data.decode()}")
        # Aqui processamos e validamos o cliente, enviamos a chave simétrica
        conn.close()


if __name__ == "__main__":
    server = Server("127.0.0.1", 65432)
    server.main()
