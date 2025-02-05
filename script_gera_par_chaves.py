import json
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# Lista de participantes com CPFs de 1 a 10
participantes = [{"cpf": str(i)} for i in range(1, 11)]

dados_client = {"participantes": []}
dados_server = {"participantes": []}

for participante in participantes:
    # Gerar par de chaves RSA
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    
    # Serializar chave privada
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()
    
    # Serializar chave pública
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    
    # Adicionar ao JSON de privados
    dados_client["participantes"].append({
        "cpf": participante["cpf"],
        "chave_privada": private_pem
    })
    
    # Adicionar ao JSON de públicos
    dados_server["participantes"].append({
        "cpf": participante["cpf"],
        "chave_publica": public_pem
    })

# Salvar os dados em arquivos JSON
with open("dados_client.json", "w", encoding="utf-8") as f:
    json.dump(dados_client, f, indent=4)

with open("dados_server.json", "w", encoding="utf-8") as f:
    json.dump(dados_server, f, indent=4)

print("Chaves geradas e salvas com sucesso!")
