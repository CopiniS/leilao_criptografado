import socket
import struct
import json
import criptografia
import threading

class Client:
    def __init__(self, hostServer: str, portServer: int):
        self.HOST = hostServer  # Endereço IP do servidor
        self.PORT = portServer  # Porta do servidor
        self.PORT_LANCES = None
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.meu_endereco = None
        self.multicast_address = None
        self.cpf = None
        self.chave_privada = None
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

    def buscaChavePrivada(self, cpf):
        with open('dados_privados.json', 'r', encoding='utf-8') as file:
            json_data = json.load(file)
            participantes = json_data['participantes']
            for p in participantes:
                if p['cpf'] == cpf:
                    self.chave_privada = p['chave_privada']

    def envia_requisicao_entrada(self, cpf: str):
        try:
            self.client_socket.connect((self.HOST, self.PORT))
            self.cpf = cpf
            self.buscaChavePrivada(cpf)
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
            textoClaro = criptografia.descriptografaAsimetrica(textoCriptografado, self.chave_privada)
            dados_json = json.loads(textoClaro) 

            self.erro = dados_json['erro']
            if not dados_json['sucesso']:
                return False

            self.multicast_address = dados_json['data']["endereco_multicast"]
            self.chave_simetrica = dados_json['data']["chave_simetrica"]
            self.PORT_LANCES = dados_json['data']["port_lances"]
            
            print(f"Endereço multicast recebido: {self.multicast_address}")
            print(f"Chave simétrica recebida: {self.chave_simetrica}")
            self.entra_multicast()
            return True
        except Exception as e:
            print(f"Erro ao receber dados de entrada: {e}")
            return False


    def envia_lance(self, lance):
        try:
            print('log 1')
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.HOST, self.PORT_LANCES))
            dados = {"lance": lance, "cpf_no_lance": self.cpf}
            texto_claro = json.dumps(dados)  
            texto_criptografado = criptografia.criptografaSimetrica(texto_claro, self.chave_simetrica)
            print('log 2')
            print('enviando esse texto:', texto_criptografado)
            client_socket.sendall(texto_criptografado.encode('utf-8'))
            print('enviado o lance: ', lance)
            return self.recebe_confirmacao_lance_unicast(client_socket)
        except Exception as e:
            print(f"Erro ao enviar requisição: {e}")
            return False
        finally:
            client_socket.close()


    def recebe_confirmacao_lance_unicast(self, client_socket):
        try:
            data = client_socket.recv(1024)  # Recebe os dados sem criptografia
            textoCriptografado = data.decode('utf-8')
            textoClaro = criptografia.descriptografaSimetrica(textoCriptografado, self.chave_simetrica)
            dados_json = json.loads(textoClaro) 
            print('recebido confirmação lance: ', dados_json)
            return dados_json
        except Exception as e:
            print(f"Erro ao enviar lance: {e}")
            return False


    def recebe_infos_produto_leiloado(self):
        if not self.multicast_address:
            print("Endereço multicast não definido.")
            return
        print(f"Endereço multicast: {self.multicast_address}")

        recepcao_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        recepcao_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        recepcao_socket.bind(("0.0.0.0", 5007))

        grupo = socket.inet_aton(self.multicast_address[0])  # Pega apenas o IP
        mreq = struct.pack("4sL", grupo, socket.INADDR_ANY)
        recepcao_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        while True:
            data, addr = recepcao_socket.recvfrom(1024)
            textoCriptografado = data.decode('utf-8')
            textoClaro = criptografia.descriptografaSimetrica(textoCriptografado, self.chave_simetrica)

            dados_json = json.loads(textoClaro)

            self.leilao['produto'] = dados_json['data']['produto']
            self.leilao['tempo'] = dados_json['data']['tempo']
            self.leilao['lance_atual'] = dados_json['data']['maior_lance']
            self.leilao['step_lances'] = dados_json['data']['step_lances']
            self.finalizado = dados_json['data']['finalizado']

    def entra_multicast(self):
        print(f"Entrando no grupo multicast: {self.multicast_address}")
        thread = threading.Thread(target=self.recebe_infos_produto_leiloado, daemon=True)
        thread.start()
