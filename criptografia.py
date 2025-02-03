from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad
import base64

def criptografaSimetrica(textoClaro: str, chave: str) -> str:
    chave_bytes = chave.encode("utf-8").ljust(16, b'0')[:16]  # Ajusta a chave para 16 bytes
    cipher = AES.new(chave_bytes, AES.MODE_CBC)
    iv = cipher.iv  # Vetor de inicialização
    textoCriptografado = cipher.encrypt(pad(textoClaro.encode("utf-8"), AES.block_size))
    return base64.b64encode(iv + textoCriptografado).decode("utf-8")

def descriptografaSimetrica(textoCriptografado: str, chave: str) -> str:
    chave_bytes = chave.encode("utf-8").ljust(16, b'0')[:16]
    dados = base64.b64decode(textoCriptografado)
    iv = dados[:16]  # Obtém o IV
    textoCriptografado = dados[16:]
    cipher = AES.new(chave_bytes, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(textoCriptografado), AES.block_size).decode("utf-8")

def criptografaAssimetrica(textoClaro: str, chave_publica: str) -> str:
    chave = RSA.import_key(chave_publica)
    cipher = PKCS1_OAEP.new(chave)
    textoCriptografado = cipher.encrypt(textoClaro.encode("utf-8"))
    return base64.b64encode(textoCriptografado).decode("utf-8")

def descriptografaAsimetrica(textoCriptografado: str, chave_privada: str) -> str:
    chave = RSA.import_key(chave_privada)
    cipher = PKCS1_OAEP.new(chave)
    dados = base64.b64decode(textoCriptografado)
    return cipher.decrypt(dados).decode("utf-8")
