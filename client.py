import socket

UDP_address = '192.168.56.101'
UDP_port = 6789

#UDP socket setup
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


#UDP connect
def HELLO (clientID_A):
    #initiate client authentication with server

    return

def RESPONSE (clientID, res):
    #response to challenge

    return

#TCP connect
def CONNECT (randCookie):
    
    return

def CHAT_REQUEST (clientID_B):
    #request for chat session with clientB

    return

def END_REQUEST (sessionID):
    #request to terminate chat session

    return

def CHAT (sessionID, message):

    return

def HISTORY_REQ (clientID_B):
    
    return