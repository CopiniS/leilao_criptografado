import socket
import struct

class Client:
    def __init__(self, hostServer: str, portServer: int):
        self.HOST = hostServer  # Endereço IP do servidor
        self.PORT = portServer  # Porta do servidor
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.multicast_address = None
        self.chave_simetrica = None

    def main(self):
        self.client_socket.connect((self.HOST, self.PORT))
        
        # Envia uma mensagem para o servidor
        mensagem = "Olá, servidor!"
        self.client_socket.sendall(mensagem.encode('utf-8'))
        
        # Recebe a resposta do servidor
        data = self.client_socket.recv(1024)
        print(f"Resposta do servidor: {data.decode('utf-8')}")
        
        self.client_socket.close()

    def envia_requisicao_entrada(self, mensagem: str):
        try:
            self.client_socket.connect((self.HOST, self.PORT))
            self.client_socket.sendall(mensagem.encode('utf-8'))
            self.recebe_dados_entrada()
        except Exception as e:
            print(f"Erro ao enviar requisição: {e}")
        finally:
            self.client_socket.close()

    def recebe_dados_entrada(self):
        try:
            data = self.client_socket.recv(1024)  # Recebe os dados sem criptografia
            endereco_multicast, chave_simetrica = data.decode('utf-8').split('|')
            self.multicast_address = endereco_multicast
            self.chave_simetrica = chave_simetrica.encode('utf-8')
            
            print(f"Endereço multicast recebido: {self.multicast_address}")
            print(f"Chave simétrica recebida: {self.chave_simetrica}")
        except Exception as e:
            print(f"Erro ao receber dados de entrada: {e}")

    def recebe_infos_produto_leiloado(self):
        if not self.multicast_address:
            print("Endereço multicast não definido.")
            return

        recepcao_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        recepcao_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        recepcao_socket.bind((self.multicast_address, 5007))
        
        grupo = socket.inet_aton(self.multicast_address)
        mreq = struct.pack("4sL", grupo, socket.INADDR_ANY)
        recepcao_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
        while True:
            data, addr = recepcao_socket.recvfrom(1024)
            print(f"Informações do leilão recebidas de {addr}: {data.decode('utf-8')}")

    def entra_multicast(self):
        print(f"Entrando no grupo multicast: {self.multicast_address}")
        self.recebe_infos_produto_leiloado()
