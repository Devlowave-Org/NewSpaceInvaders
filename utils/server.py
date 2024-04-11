import socket
from threading import Thread
import time
from dataclasses import dataclass
import json
import pickle


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
        self.pseudo = None
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
                self.ppseudo = handshake.split(" ")[1]
                self.lobby.ready[self.id] = {"pseudo": self.pseudo, "status": "connected"}
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

        while req:
            req = self.recv_data()
            if req == "/jlist":
                self.send_data(json.dumps(self.lobby.clients))

            if req == "/create" and self.lobby.ready[self.id]["status"] != Status.ingame:
                # on va créer une partie et le mettre dedans.
                self.create_party()

            
            if "/join" in req and self.lobby.ready[self.id]["status"] != Status.ingame:
                try:
                    p_id = req.split(" ")[1]
                    p_id = int(p_id)
                    party = self.lobby.party[p_id]
                    self.join_party(party)
                except IndexError or ValueError:
                    self.close()
                
        self.close()
    
    def join_party(self, party: object):
        """
        Un client veut rejoindre une partie qui n'est pas pleine.
        Il va devoir nous transmettre son objet vaisseau
        On va d'abord récupérer la partie grâce à l'ID
        """
        self.send_data("player_object")
        p_object = self.recv_object()
        match party:
            case party if not party.player1:
                party.player1 = p_object
            case party if not party.player2:
                party.player2 = p_object
            case _:
                self.close()
                
        
            # Alors on peut lui demander son objet
    

    def create_party(self):
        # On va lui répondre en lui demandant sont objet
        self.send_data("main_object")
        # Le p_object contient à la fois le Joueur et le BackGround.
        p_object = self.recv_object()

        if not p_object:
            self.close
        
        party = Party(player1=p_object.player, player2=None, backgound=p_object.background, level=0, status=Status.waiting)
        self.lobby.party.append(party)
        self.lobby.ready[self.id]["status"][Status.waiting]


    def recv_data(self):
        data = self.s_client.recv(1024).decode("utf-8")
        if data == '':
            return None
        return data
    
    def recv_object(self):
        obj = self.s_client.recv(1024)
        if not obj:
            return None
        obj = pickle.loads(obj)
        return obj


    def send_data(self, data: str):
        self.s_client.send(data.encode("utf-8"))

    def close(self):
        self.s_client.close()
        self.lobby.ready.pop(self.id, None)
        self.lobby.delitem(self.c_address)
        exit()


@dataclass
class Lobby:
    clients: list
    ready: dict
    party: list

    def delitem(self, key):
        self.clients.remove(key)

@dataclass
class Party:
    player1: object
    player2: object
    backgound: object
    level: int
    status: str


class Status:
    ingame = "ingame"
    waiting = "waiting for a mate"
    connected = "connected"
    ready = "ready"

if __name__ == "__main__":
    server = Server("", 3489)
    server.pool()
