import socket
import threading
import time
import rich
import api
import json
import random
from colorama import Fore, Style

import utils

# Initialisation du serveur sur le port `62222`
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", 62222))
sock.listen()

# Création du lobby et du tableau des parties
lobby = {}
party = {}


def client_init(client_jouer: socket.socket, client_address: tuple):
    try:
        handle_client(client_jouer, client_address)
    except OSError or KeyError or ValueError:
        print(Fore.RED + "Un client nous a quitté...")
        print(Style.RESET_ALL)
        if client_address in lobby:
            # On vérifie qu'il n'est pas dans une partie
            if lobby[client_address]["partie_id"]:
                print("Suppression d'un client d'une PARTIE")
                party[lobby[client_address]["partie_id"]]["joueurs"].remove(client_address)
            lobby.pop(client_address)
        client_jouer.close()


def handle_client(client_jouer: socket.socket, client_address):
    print(Fore.BLUE + f"Client : {client_address}")
    message = None
    while message != "/quit":
        data = client_jouer.recv(1024).decode("utf-8")
        print(Fore.BLUE + f"Message de {client_address} : {data}")
        print(Style.RESET_ALL)
        if data == "":
            print("Message vide")
            client_jouer.close()
            message = "/quit"
            continue

        data = data.split()

        if data[0] == "/lobbylist":
        # On lui renvoie tous les joueurs du lobby
            to_return = {}
            for joueur in lobby:
                """
                {"127.0.0.1": {"pseudo": "sd", "status": "disponible", "partie_id": null}}
                """
                to_return[f"{joueur[0]}:{joueur[1]}"] = {"pseudo": lobby[joueur]["pseudo"], "status": lobby[joueur]["status"], "partie_id": lobby[joueur]["partie_id"]}
            print("Voici ce que l'on return à /lobbylist")
            rich.print(to_return)
            client_jouer.send(json.dumps(to_return).encode("utf-8"))

        if data[0] == "/partylist":
            # Retourne la liste des parties
            to_return = {}
            for partie_id in party:
                joueurs = []
                for joueur in party[partie_id]["joueurs"]:
                    joueurs.append(lobby[joueur]["pseudo"])
                to_return[partie_id] = {"joueurs": joueurs}
            print("Voici ce que l'on return à /partylist")
            rich.print(to_return)
            client_jouer.send(json.dumps(to_return).encode("utf-8"))

        if data[0] == "/lobby":
            if client_address in lobby:
                print(f"{lobby[client_address]} est déjà dans le lobby")

            else:
                print(f"Ajout de {data[1]} au lobby")
                lobby[client_address] = {"pseudo": data[1], "status": "disponible", "partie_id": None, "client": client_jouer}
            client_jouer.send(json.dumps({"message": "connected"}).encode("utf-8"))

        # Si le client ne s'enregistre pas on vérifie qu'il l'est pour pouvoir faire les autres commandes
        if client_address not in lobby:
            client_jouer.send(f"Veuillez d'abord rejoindre le lobby".encode("utf-8"))
            continue

        if data[0] == "/create":
            p_id = str(len(party) + 1)
            lobby[client_address]["status"] = "ingame"
            lobby[client_address]["partie_id"] = p_id

            party[p_id] = {"joueurs": [client_address], "jeu": None}
            client_jouer.send(json.dumps({"message": "ok", "partie_id": p_id}).encode("utf-8"))
            print("OOOK")

        elif data[0] == "/join":
            # Ici le try except essaye de lire les arguments de /join, si il n'y arrive pas il renvoie une erreur
            try:
                # Vérifions si le joueur n'est pas déjà dans une partie ET qu'il y a moins de 2 joueurs
                if client_address not in party[data[1]]["joueurs"] and len(party[data[1]]["joueurs"]) < 2:

                    party[data[1]]["joueurs"].append(client_address)
                    lobby[client_address]["partie_id"] = data[1]
                else:
                    client_jouer.send(json.dumps({"message": "error", "details": f"Vous êtes déjà dans la partie {data[1]}. /leave pour la quitter"}).encode("utf-8"))

                if len(party[data[1]]["joueurs"]) == 2:
                    # On fait les requetes API pour générer le tableau et on détermine le tour
                    tour = [random.choice(party[data[1]]["joueurs"])]

                    # On détermine leurs numéros
                    # j1 = api.ip_to_number(party[data[1]]["joueurs"][0], party[data[1]]["joueurs"])
                    # j2 = api.ip_to_number(party[data[1]]["joueurs"][1], party[data[1]]["joueurs"])

                    # On ajoute le pseudo
                    tour.append(lobby[tour[0]]["pseudo"])

                    """
                    {"joueurs": [["127.0.0.1", 45512], ["127.0.0.1", 45522]], "jeu": {"board": [[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0]], "tour": [("127.0.0.1", 45512), "position": 0]}}
                    """
                    party[data[1]]["jeu"] = {"board": api.board(), "game": api.Game(party[data[1]]["joueurs"], api.board(), tour[0]), "position": 0}
                client_jouer.send(json.dumps({"message": "ok"}).encode("utf-8"))

            except KeyError:
                client_jouer.send(json.dumps({"message": "error", "details": "Veuillez renseigner un idientifiant valide"}).encode("utf-8"))

        # Et là c'est quand le client est prêt à jouer et qu'il attend
        elif data[0] == "/waitpeople":
            p_id = lobby[client_address]["partie_id"]
            if not p_id:
                client_jouer.send(json.dumps({"message": "error", "details": "Veuillez d'abord rejoindre une partie"}).encode("utf-8"))
            else:
                while len(party[p_id]["joueurs"]) != 2:
                    utils.send_json(client_jouer, {"message": "/waitpeople"})
                    # Il faut régler le fait qu'un client peut quitter ici
                    data = utils.recv_simple(client_jouer)
                    if data != "/waitpeople":
                        raise OSError
                    # On attend qu'un joueur rejoigne la partie
                    print(party)
                    time.sleep(1)
                jouer(p_id, client_jouer, client_address)
    print("Fermeture d'un client")
    raise OSError


def jouer(partie_id, client_jouer: socket.socket, client_address):
    # Une fois que la partie est crée et que les deux joueurs sont dedans
    game = party[partie_id]["jeu"]["game"]
    print("<---Board actuel--->")
    print(game.board)
    to_send = {"message": "ok", "joueurs": party[partie_id]["joueurs"]} | {"board": party[partie_id]["jeu"]["board"], "position": party[partie_id]["jeu"]["position"]} | {"you": client_address} | {"tour": game.player_turn()}
    client_jouer.send(json.dumps(to_send).encode("utf-8"))
    while True:
        data = utils.recv_json(client_jouer)
        if data is None:
            client_jouer.close()
            continue
        print(f"Data from {client_address}\n {data}")

        if data["message"] == "/waitgame":
            position = 0
            board = data["board"]
            # print(f"WAIT : {game.board} \n {board}")
            while game.board == board:
                # On lui renvoie un message de confirmation d'attente toute les secondes
                # On peut aussi lui envoyer les positions de l'autre personne qui joue

                if party[partie_id]["jeu"]["position"] != position:
                    position = party[partie_id]["jeu"]["position"]
                    utils.send_json(client_jouer, {"message": "/waitgame", "position": position})
                    # Et on attend sa réponse
                    data = utils.recv_json(client_jouer)
                time.sleep(0.2)

            party[partie_id]["jeu"]["position"] = 0
            print(lobby[client_address]["pseudo"] + " Est sortie du /WAITGAME")

            if game.check_endgame():
                print(f"La partie est fini pour {client_address} (DANS LA BOUCLE /WAIT)")
                fin_partie(game, client_jouer, client_address)
            else:
                print(f"<--{client_address} peut JOUER-->")
                client_jouer.send(json.dumps({"message": "/continue", "board": game.board}).encode("utf-8"))

        if data["message"] == "/position":
            try:
                colonne = int(data["position"])
                if colonne < 0:
                    colonne = 0
                if colonne > 6:

                      colonne = 6
                party[partie_id]["jeu"]["position"] = colonne

            except ValueError or KeyError:
                utils.send_json(client_jouer, {"message": "error", "board": game.board, "details": "/position n'aime pas votre coup"})

        if data["message"] == "/play":
            if client_address != game.player_turn():
                print(f"left {client_address} // right {game.player_turn()}")
                client_jouer.send("Error : Pas ton tour connard".encode("utf-8"))
                # Une fois qu'on lui a répondu, on attend un nouveau message de sa part
                continue
            try:
                colonne = int(data["coup"])
                if colonne < 0:
                    colonne = 0
                if colonne > 6:
                    colonne = 6

                if game.check_column(column_number=colonne):
                    nboard = game.drop_piece(column_number=colonne)
                    game.board = nboard
                    if game.check_endgame():
                        print(f"La partie est fini pour {client_address}")
                        fin_partie(game,client_jouer, client_address)
                    else:
                        print(f"<---Nouveau plateau--->\n{nboard}")
                        utils.send_json(client_jouer, {"message": "/waitgame", "board": nboard})
            except ValueError or KeyError:
                client_jouer.send(json.dumps({"message": "error", "board": game.board, "details": "Veuillez entrer un bon numéro"}).encode("utf-8"))


def fin_partie(game, client_in_end, client_address):
    client_in_end.send(json.dumps({"message": "/endgame", "board": game.board}).encode("utf-8"))
    party[lobby[client_address]["partie_id"]]["joueurs"].remove(client_address)
    print("On a sortie un joueur de la partie")
    lobby[client_address]["status"] = "disponible"
    lobby[client_address]["partie_id"] = None
    handle_client(client_in_end, client_address)


error = False
while not error:
    print(Fore.GREEN + "Boucle en attente d'un client...")
    print(Style.RESET_ALL)
    client, client_address_while = sock.accept()
    try:
        threading.Thread(target=client_init, args=(client, client_address_while)).start()
    except OSError or IndexError as e:
        print(utils.error_log(e))
        client.close()
        print(Fore.RED + "Un thread nous a quitté")
        print(Style.RESET_ALL)

    print("Le thread a été lancé")
