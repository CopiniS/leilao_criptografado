# client_interface.py
import tkinter as tk
from client import Client

def conectar_servidor():
    host = entry_host.get()
    port = int(entry_port.get())

    cliente = Client()
    output_text.insert(tk.END, f"Conectando ao servidor {host}:{port}...\n")

    # Conecta ao servidor (chama a função principal do cliente)
    cliente.main(host, port)

def enviar_lance():
    valor_lance = entry_lance.get()
    output_text.insert(tk.END, f"Lance enviado: R${valor_lance}\n")

    # Aqui você poderia chamar uma função específica do cliente para enviar o lance

# Configuração da janela principal
top = tk.Tk()
top.title("Cliente de Leilão")

# Campos para configurar a conexão com o servidor
tk.Label(top, text="Host do Servidor:").pack()
entry_host = tk.Entry(top)
entry_host.insert(0, "127.0.0.1")
entry_host.pack()

tk.Label(top, text="Porta do Servidor:").pack()
entry_port = tk.Entry(top)
entry_port.insert(0, "65432")
entry_port.pack()

tk.Button(top, text="Conectar ao Servidor", command=conectar_servidor).pack()

# Campos para enviar lances
tk.Label(top, text="Valor do Lance:").pack()
entry_lance = tk.Entry(top)
entry_lance.pack()

tk.Button(top, text="Enviar Lance", command=enviar_lance).pack()

# Saída de logs
tk.Label(top, text="Logs:").pack()
output_text = tk.Text(top, height=10, width=50)
output_text.pack()

# Inicia o loop da interface
top.mainloop()
