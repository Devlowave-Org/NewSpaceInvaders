import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 3489))
client.send("/handshake timtonix".encode("utf-8"))
print(client.recv(1024))
client.send("/plist".encode("utf-8"))
print(client.recv(1024))
