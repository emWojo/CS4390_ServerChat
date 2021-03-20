import socket
import bcrypt
from secrets import token_urlsafe
import hashlib
from aesClass import aesCipher
from utils import messageDict

#UDP socket setup
#UDP_address = '192.168.56.101'
#UDP_port = 6789
#server_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#server_UDP.bind((UDP_address, UDP_port))
#server_UDP.listen


#UDP Socket
def CHALLENGE (socket, clientID, addr, rand):
    #send rand to client to authenticate itself
    resp = "CHALLENGE "
    message = resp.encode() + rand
    socket.sendto(message, addr)

#UDP Socket
def AUTH_SUCCESS (socket, clientID, addr, randCookie, password, salt, portNumber):
    #client authentication successful
    #send randCookie and TCP portNumber to client
    # TODO: Move Encryption to Server_TCP.py
    resp = "AUTH_SUCCESS " # resp = json.stringfy(object)
    resp += str(portNumber) + " "
    message = resp + randCookie
    ck_a = hashlib.pbkdf2_hmac('SHA256', password.encode(), salt, 100000)
    machine = aesCipher(ck_a)
    encryptedMessage = machine.encryptMessage(message)
    auth_type = 'as '.encode()
    encryptedMessage = auth_type + encryptedMessage
    socket.sendto(encryptedMessage, addr)

#UDP Socket
def AUTH_FAIL (socket, clientID, addr):
    #client authentication fail
    resp = "AUTH_FAIL "
    message = resp.encode('utf-8')
    socket.sendto(message, addr)

#TCP Socket
def CONNECTED (socket, message):
    #notify client it has been connected
    socket.send(message)

def CHAT_STARTED (socket, sessionID, clientID_B):
    #notify clientA that chat session with clientB has started
    #assign sessionID to the session

    return

def UNREACHABLE (socket, clientID_B):
    #notify clientA clientB is not available for chat

    return

def END_NOTIF (socket, sessionID):
    #notify clients in the session that the session has been terminated

    return

def HISTORY_RES (socket, clientID, message):
    
    return 0
