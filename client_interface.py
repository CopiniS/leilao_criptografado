import tkinter as tk
from tkinter import messagebox
from threading import Thread
import time
from client import Client  # Importa a classe Client

class AuctionClientInterface:
    def __init__(self):
        self.client = Client("127.0.0.1", 65432, self.load_private_key())
        self.root = tk.Tk()
        self.root.title("Cliente de Leilão")
        self.create_access_screen()
    
    def load_private_key(self):
        with open("chave_privada.pem", "rb") as f:
            return f.read()
    
    def create_access_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Acessar Leilão", font=("Arial", 16)).pack(pady=10)
        
        tk.Label(self.root, text="CPF:").pack()
        self.cpf_entry = tk.Entry(self.root)
        self.cpf_entry.pack()
        
        tk.Button(self.root, text="Acessar", command=self.access_auction).pack(pady=10)
    
    def access_auction(self):
        cpf = self.cpf_entry.get()
        if not cpf:
            messagebox.showerror("Erro", "Digite um CPF válido.")
            return
        
        self.client.envia_requisicao_entrada(cpf)
        
        if self.client.multicast_address:
            self.create_auction_screen()
        else:
            messagebox.showerror("Erro", "Falha ao acessar leilão.")
    
    def create_auction_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Leilão Ativo", font=("Arial", 16)).pack(pady=10)
        
        self.label_tempo = tk.Label(self.root, text="Tempo restante: 00:00", font=("Arial", 14))
        self.label_tempo.pack()
        
        self.label_produto = tk.Label(self.root, text="Produto: Carregando...", font=("Arial", 14))
        self.label_produto.pack()
        
        self.label_lance = tk.Label(self.root, text="Lance atual: Carregando...", font=("Arial", 14))
        self.label_lance.pack()
        
        tk.Label(self.root, text="Seu lance:").pack()
        self.lance_entry = tk.Entry(self.root)
        self.lance_entry.pack()
        
        tk.Button(self.root, text="Enviar Lance", command=self.send_bid).pack(pady=10)
        
        # Iniciar thread para receber dados do leilão
        Thread(target=self.update_auction_data, daemon=True).start()
    
    def update_auction_data(self):
        while True:
            try:
                data = self.client.recebe_infos_produto_leiloado()
                if data:
                    produto, tempo, valor = data.split('|')
                    self.label_produto.config(text=f"Produto: {produto}")
                    self.label_tempo.config(text=f"Tempo restante: {tempo}")
                    self.label_lance.config(text=f"Lance atual: {valor}")
            except Exception as e:
                print(f"Erro ao atualizar leilão: {e}")
            time.sleep(1)
    
    def send_bid(self):
        lance = self.lance_entry.get()
        if not lance.isnumeric():
            messagebox.showerror("Erro", "Digite um valor válido para o lance.")
            return
        
        # Simulação de envio de lance (implementar na classe Client)
        print(f"Enviando lance: {lance}")
        
    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AuctionClientInterface()
    app.run()
