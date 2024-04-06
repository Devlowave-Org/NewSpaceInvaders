import socket
from threading import Thread
import time
from dataclasses import dataclass


class Server:
    def __init__(self, ip, port: int):
        self.lobby = Lobby([])
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ip, port))
        self.sock.listen()
        self.crash = False


    def pool(self):
        while not self.crash:
            print("En attente d'un client...")
            client, client_address = self.sock.accept()
            try:
                Thread(target=ClientThread, args=(client, client_address, self.lobby)).start()
            except OSError or IndexError as e:
                print("Erreur lors de la réception d'un client.")
                client.close()

class ClientThread:
    def __init__(self, s_client: socket.socket, c_address, lobby: object):
        self.lobby = lobby
        self.s_client = s_client
        self.c_address = c_address
        self.handle_client()

    def handle_client(self):
        if self.c_address in self.lobby.clients:
            print("Déja Connecté")

@dataclass
class Lobby:
    clients: list

    def __delitem__(self, key):
        self.clients.remove(key)

@dataclass
class Party:
    player1: list
    player2: list
    pos1: list
    pos2: list
    level: int


if __name__ == "__main__":
    server = Server("", 3489)
    server.pool()
