import tkinter as tk
from tkinter import messagebox
import socket
import threading
import json
from client import Client

class LeilaoCliente:
    def __init__(self, root):
        self.client = Client("127.0.0.1", 65432)
        self.root = root
        self.root.title("Leilão Online")
        self.cpf = None
        self.multicast_endereco = None
        self.chave = None
        self.build_login_screen()

    def build_login_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        tk.Label(self.root, text="Digite seu CPF:").pack(pady=5)
        self.cpf_entry = tk.Entry(self.root)
        self.cpf_entry.pack(pady=5)
        
        self.enviar_button = tk.Button(self.root, text="Entrar", command=self.enviar_cpf)
        self.enviar_button.pack(pady=5)

    def enviar_cpf(self):
        cpf = self.cpf_entry.get()
        if not cpf:
            messagebox.showerror("Erro", "CPF não pode estar vazio.")
            return
        
        # Simula o envio para o servidor
        if self.client.envia_requisicao_entrada():
            self.multicast_endereco = resposta["endereco_multicast"]
            self.chave = resposta["chave_simetrica"]
            self.build_leilao_screen()
        else:
            messagebox.showerror("Erro", "CPF inválido ou não autorizado.")

    def build_leilao_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.tempo_label = tk.Label(self.root, text=f"Tempo restante: {self.client.leilao["tempo"]}")
        self.tempo_label.pack(pady=5)
        
        self.produto_label = tk.Label(self.root, text=f"Produto: {self.client.leilao["produto"]}")
        self.produto_label.pack(pady=5)
        
        self.lance_label = tk.Label(self.root, text=f"Lance atual: {self.client.leilao["lanceAtual"]}")
        self.lance_label.pack(pady=5)
        
        tk.Label(self.root, text="Digite seu lance:").pack(pady=5)
        self.lance_entry = tk.Entry(self.root)
        self.lance_entry.pack(pady=5)
        
        self.enviar_lance_button = tk.Button(self.root, text="Enviar Lance", command=self.enviar_lance)
        self.enviar_lance_button.pack(pady=5)
        
        # Simular recebimento de atualizações do leilão
        self.thread_receber_multicast = threading.Thread(target=self.receber_multicast, daemon=True)
        self.thread_receber_multicast.start()

    def enviar_lance(self):
        lance = self.lance_entry.get()
        if not lance.isdigit():
            messagebox.showerror("Erro", "Insira um valor válido.")
            return
        
        # Simular envio do lance para o servidor
        print(f"Lance de R${lance} enviado!")
        messagebox.showinfo("Sucesso", f"Lance de R${lance} enviado com sucesso!")

    def atualizar_tela(self, dados):
        self.tempo_label.config(text=f"Tempo restante: {dados['tempo']}")
        self.produto_label.config(text=f"Produto: {dados['produto']}")
        self.lance_label.config(text=f"Lance atual: {dados['lance']}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LeilaoCliente(root)
    root.mainloop()
