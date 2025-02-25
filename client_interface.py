import tkinter as tk
from tkinter import messagebox
import socket
import threading
import json
from client import Client

class LeilaoCliente:
    def __init__(self, root):
        self.client = Client()
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
        
        if self.client.envia_requisicao_entrada(cpf):
            self.build_leilao_screen()
        else:
            messagebox.showerror("Erro", self.client.erro)
            self.client.erro = None

    def build_leilao_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.tempo_label = tk.Label(self.root, text=f"Tempo restante: {self.client.leilao['tempo']}")
        self.tempo_label.pack(pady=5)
        
        self.produto_label = tk.Label(self.root, text=f"Produto: {self.client.leilao['produto']}")
        self.produto_label.pack(pady=5)
        
        self.lance_label = tk.Label(self.root, text=f"Lance atual: {self.client.leilao['lance_atual']}")
        self.lance_label.pack(pady=5)
        
        tk.Label(self.root, text="Digite seu lance:").pack(pady=5)
        self.lance_entry = tk.Entry(self.root)
        self.lance_entry.pack(pady=5)
        
        self.enviar_lance_button = tk.Button(self.root, text="Enviar Lance", command=self.enviar_lance)
        self.enviar_lance_button.pack(pady=5)

        # Inicia a atualização automática
        self.atualiza_labels()

    def atualiza_labels(self):
        """Atualiza os labels da interface com os novos dados do leilão."""
        self.tempo_label.config(text=f"Tempo restante: {self.client.leilao['tempo']}")
        self.produto_label.config(text=f"Produto: {self.client.leilao['produto']}")
        self.lance_label.config(text=f"Lance atual: {self.client.leilao['lance_atual']}")
        
        # Agendar próxima atualização em 1 segundo (1000 ms)
        self.root.after(1000, self.atualiza_labels)

    def enviar_lance(self):
        lance = self.lance_entry.get()
        if not lance.isdigit():
            messagebox.showerror("Erro", "Insira um valor válido.")
            return
        resposta = self.client.envia_lance(lance)
        if(not resposta):
            messagebox.showerror("Erro", "Servidor nao retornou a mensagem")
            self.client.erro = None
        elif not resposta["sucesso"]:
            messagebox.showerror("Erro", resposta["erro"])
        else:
            messagebox.showinfo("Sucess", "O seu lance foi aceito!")


    def atualizar_tela(self, dados):
        self.tempo_label.config(text=f"Tempo restante: {dados['tempo']}")
        self.produto_label.config(text=f"Produto: {dados['produto']}")
        self.lance_label.config(text=f"Lance atual: {dados['lance']}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LeilaoCliente(root)
    root.mainloop()
