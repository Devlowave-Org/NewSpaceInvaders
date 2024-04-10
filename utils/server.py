import socket
from threading import Thread
import time
from dataclasses import dataclass
import json


class Server:
    def __init__(self, ip, port: int):
        self.lobby = Lobby([], {}, [])
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
                print("Erreur lors de la réception d'un client." + e)
                client.close()

class ClientThread:
    def __init__(self, s_client: socket.socket, c_address, lobby: dataclass):
        self.lobby = lobby
        self.s_client = s_client
        self.c_address = c_address
        self.id = c_address[0] + "@" + str(c_address[1])
        self.handle_client()

    def handle_client(self):
        print(f"Un client a HANDLE: {self.c_address}")
        if self.c_address in self.lobby.clients:
            print("Déja Connecté")
        else:
            self.lobby.clients.append(self.c_address)
        # On va d'abord attendre un message avant de l'inscrire
        handshake = self.recv_data()
        if "/handshake" in handshake:
            try:
                pseudo = handshake.split(" ")[1]
                self.lobby.ready[self.id] = {"pseudo": pseudo, "status": "connected"}
                self.send_data("connected to the server")
                self.start_menu()
            except IndexError:
                self.close()
        else:
            self.close()


    def start_menu(self):
        """
        L'utilisateur peut
        -> Rejoindre une partie
        -> Créer une partie
        -> Lister les parties
        :return: on retourne rien, on envoie des paquets
        """
        req = self.recv_data()
        if req == "/jlist":
            self.send_data(json.dumps(self.lobby.clients))

        if req == "/create" and self.lobby.ready[self.id]["status"] != "ingame":
            # on va créer une partie
            pass

        if "/join" in req and self.lobby.ready[self.id]["status"] != "ingame":
            pass


    def recv_data(self):
        data = self.s_client.recv(1024).decode("utf-8")
        if data == '':
            return None
        return data

    def send_data(self, data: str):
        self.s_client.send(data.encode("utf-8"))

    def close(self):
        self.s_client.close()
        self.lobby.ready.pop(self.id, None)
        self.lobby.delitem(self.c_address)


@dataclass
class Lobby:
    clients: list
    ready: dict
    party: list

    def delitem(self, key):
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
