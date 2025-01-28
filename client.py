
import socket

class Client:
    def main(self, hostServer: str, portServer: int):
        HOST = hostServer  # Endereço IP do servidor
        PORT = portServer         # Porta do servidor

        # Criação do socket do cliente
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))

        # Envia uma mensagem para o servidor
        mensagem = "Olá, servidor!"
        client_socket.sendall(mensagem.encode('utf-8'))

        # Recebe a resposta do servidor
        data = client_socket.recv(1024)
        print(f"Resposta do servidor: {data.decode('utf-8')}")

        client_socket.close()

    def enviaRequisicaoEntrada():
        pass

    def recebeDadosEntrada():
        pass

    def recebeInfosProdutoLeiolado():
        pass

    def entraMulticast():
        pass

    def descriptografaComChavePrivada():
        pass