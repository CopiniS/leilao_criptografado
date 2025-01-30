import tkinter as tk
from tkinter import messagebox
from threading import Thread
from server import Server
from datetime import timedelta
import time

class AuctionInterface:
    def __init__(self):

        self.server = Server("127.0.0.1", 65432)
        # Inicia o servidor em uma thread separada
        Thread(target=self.server.main, daemon=True).start()

        
        self.root = tk.Tk()
        self.root.title("Servidor de Leilão")
        self.create_start_screen()


    def create_start_screen(self):
        # Configuração da tela inicial
        self.clear_screen()
        tk.Label(self.root, text="Publicar Item", font=("Arial", 16)).pack(pady=10)

        tk.Label(self.root, text="Nome do Produto:").pack()
        self.nome_produto = tk.Entry(self.root)
        self.nome_produto.pack()

        tk.Label(self.root, text="Lance Inicial:").pack()
        self.lance_inicial = tk.Entry(self.root)
        self.lance_inicial.pack()

        tk.Label(self.root, text="Step de Lances:").pack()
        self.step_lances = tk.Entry(self.root)
        self.step_lances.pack()

        tk.Label(self.root, text="Tempo (em segundos):").pack()
        self.tempo = tk.Entry(self.root)
        self.tempo.pack()

        tk.Button(self.root, text="Iniciar Leilão", command=self.start_auction).pack(pady=10)

    def start_auction(self):
        # Obtém os dados do formulário e inicia o leilão
        try:
            nome = self.nome_produto.get()
            lance_inicial = float(self.lance_inicial.get())
            step_lances = float(self.step_lances.get())
            tempo = int(self.tempo.get())

            if not nome or lance_inicial <= 0 or step_lances <= 0 or tempo <= 0:
                raise ValueError("Valores inválidos")

            self.server.publica_item(nome, lance_inicial, step_lances, tempo)
            self.create_auction_screen()
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira valores válidos.")

    def create_auction_screen(self):
        # Configuração da tela de leilão
        self.clear_screen()
        tk.Label(self.root, text="Leilão Ativo", font=("Arial", 16)).pack(pady=10)

        self.label_tempo = tk.Label(self.root, text=f"Tempo restante: {self.server.item_leilao['tempo']}", font=("Arial", 14))
        self.label_tempo.pack()

        tk.Label(self.root, text=f"Produto: {self.server.item_leilao['nome']}", font=("Arial", 14)).pack()
        self.label_lance_atual = tk.Label(self.root, text=f"Lance atual: {self.server.item_leilao['maior_lance']}", font=("Arial", 14))
        self.label_lance_atual.pack()
        self.label_usuario = tk.Label(self.root, text=f"Usuário: {self.server.item_leilao['usuario']}", font=("Arial", 14))
        self.label_usuario.pack()

        # Atualização do tempo restante
        self.update_timer()

    def update_timer(self):
        if self.server.leilao_ativo:
            tempo = self.server.item_leilao['tempo']
            if tempo.total_seconds() > 0:
                self.label_tempo.config(text=f"Tempo restante: {tempo}")
                self.server.item_leilao['tempo'] -= timedelta(seconds=1)
                self.root.after(1000, self.update_timer)
            else:
                self.server.leilao_ativo = False
                self.end_auction()

    def end_auction(self):
        messagebox.showinfo("Leilão Finalizado", "O leilão foi encerrado.")
        self.create_start_screen()

    def clear_screen(self):
        # Remove todos os widgets da tela
        for widget in self.root.winfo_children():
            widget.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AuctionInterface()
    app.run()
