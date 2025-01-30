import socket
import struct
import json
import criptografia

class Client:
    def __init__(self, hostServer: str, portServer: int):
        self.HOST = hostServer  # Endereço IP do servidor
        self.PORT = portServer  # Porta do servidor
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.multicast_address = None
        self.chave_simetrica = None
        self.erro = None
        self.sucesso = None
        self.finalizado = False
        self.leilao = {
            'produto': None,
            'tempo': None,
            'lance_atual': None,
            'step_lances': None,
        }

    def main(self):
        self.client_socket.connect((self.HOST, self.PORT))
        
        # Envia uma mensagem para o servidor
        mensagem = "Olá, servidor!"
        self.client_socket.sendall(mensagem.encode('utf-8'))
        
        # Recebe a resposta do servidor
        data = self.client_socket.recv(1024)
        print(f"Resposta do servidor: {data.decode('utf-8')}")
        
        self.client_socket.close()

    def envia_requisicao_entrada(self, cpf: str):
        try:
            self.client_socket.connect((self.HOST, self.PORT))
            dados = {"cpf": cpf}
            json_dados = json.dumps(dados)  # Converter para JSON
            self.client_socket.sendall(json_dados.encode('utf-8'))
            return self.recebe_dados_entrada()
        except Exception as e:
            print(f"Erro ao enviar requisição: {e}")
            return False
        finally:
            self.client_socket.close()

    def recebe_dados_entrada(self):
        try:
            data = self.client_socket.recv(1024)  # Recebe os dados sem criptografia
            textoCriptografado = data.decode('utf-8')
            textoClaro = criptografia.descriptografaAsimetrica(textoCriptografado, 'chave')
            dados_json = json.loads(textoClaro) 

            self.erro = dados_json['erro']
            if not dados_json['sucesso']:
                return False

            self.multicast_address = dados_json['data']["endereco_multicast"]
            self.chave_simetrica = dados_json['data']["chave_simetrica"]
            
            print(f"Endereço multicast recebido: {self.multicast_address}")
            print(f"Chave simétrica recebida: {self.chave_simetrica}")
            self.entra_multicast()
            return True
        except Exception as e:
            print(f"Erro ao receber dados de entrada: {e}")
            return False

    def envia_lance(self, lance):
        try:
            self.client_socket.connect((self.HOST, self.PORT))
            dados = {"lance": float(lance)}
            textoClaro = json.dumps(dados) 
            textoCriptografado = criptografia.criptografaSimetrica(textoClaro, self.chave_simetrica)
            self.client_socket.sendall(textoCriptografado.encode('utf-8'))
            return self.recebe_confirmacao_lance()
        except Exception as e:
            print(f"Erro ao enviar requisição: {e}")
            return False
        finally:
            self.client_socket.close()

    def recebe_confirmacao_lance(self):
        data = self.client_socket.recv(1024)  # Recebe os dados sem criptografia
        textoCriptografado = data.decode('utf-8')
        textoClaro = criptografia.descriptografaSimetrica(textoCriptografado, self.chave_simetrica)
        dados_json = json.loads(textoClaro) 

        self.erro = dados_json['erro']
        if not dados_json['sucesso']:
            return False

        self.sucesso = '[SUCESSO]: Você tem o mair lance no momento'

    def recebe_infos_produto_leiloado(self):
        if not self.multicast_address:
            print("Endereço multicast não definido.")
            return
        print(f"Endereço multicast: {self.multicast_address}")
        print('log 0')
        recepcao_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        recepcao_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        recepcao_socket.bind((self.multicast_address, 5007))
        print('log 1')
        grupo = socket.inet_aton(self.multicast_address)
        mreq = struct.pack("4sL", grupo, socket.INADDR_ANY)
        recepcao_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        print('log 2')
        while True:
            print('log 3')
            data, addr = recepcao_socket.recvfrom(1024)
            print('data aqui detrno: ', data)
            textoCriptografado = data.decode('utf-8')
            textoClaro = criptografia.descriptografaSimetrica(textoCriptografado, self.chave_simetrica)

            dados_json = json.loads(textoClaro)

            print('aqui chega com dados_json: ', dados_json)

            self.leilao['produto'] = dados_json['data']['produto']
            self.leilao['tempo'] = dados_json['data']['tempo']
            self.leilao['lance_atual'] = dados_json['data']['maior_lance']
            self.leilao['step_lances'] = dados_json['data']['step_lances']
            self.finalizado = dados_json['data']['finalizado']
            
            print(f"Informações do leilão recebidas de {addr}: {data.decode('utf-8')}")

    def entra_multicast(self):
        print(f"Entrando no grupo multicast: {self.multicast_address}")
        self.recebe_infos_produto_leiloado()
