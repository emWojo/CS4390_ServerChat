import socket
import bcrypt
from secrets import token_urlsafe
import hashlib
import time
import pickle
from utils import messageDict

UDP_address = 'localhost'
UDP_port = 6265

class clientAPI:
    def __init__(self, clientID):
        #UDP socket setup
        self.Uclient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.Uclient.connect((UDP_address, UDP_port))
        self.Tclient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientID = clientID
        self.salt = None

    #UDP connect
    def HELLO (self):
        #initiate client authentication with server
        msg = messageDict(self.clientID, "HELLO")
        self.Uclient.send(str.encode("HELLO " + str(self.clientID)))

    def RESPONSE (self, password, salt):
        #response to challenge
        saltyPass = bcrypt.hashpw(str(password).encode(), salt)
        message = str.encode("RESPONSE ")
        msg = messageDict(self.clientID, "RESPONSE", hashedPassword=saltyPass)
        self.Uclient.send(message + saltyPass)
        self.salt = salt

    def CONNECT (self, encMessage):
        totMessage = str(self.clientID).encode() + encMessage
        self.Tclient.send(totMessage)

    def CHAT_REQUEST (self, clientID_B):
        #request for chat session with clientB
        #TODO
        return

    def END_REQUEST (self, sessionID):
        #request to terminate chat session
        #TODO
        return

    def CHAT (self, sessionID, message):
        #TODO
        return

    def HISTORY_REQ (self, clientID_B):
        #TODO
        return
        