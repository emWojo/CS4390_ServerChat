import socket

#UDP socket setup
UDP_address = '192.168.56.101'
UDP_port = 6789
server_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_UDP.bind((UDP_address, UDP_port))
server_UDP.listen


#UDP connect
def CHALLENGE (rand):
    #send rand to client to authenticate itself

    return 
def AUTH_SUCCESS (randCookie, portNumber):
    #client authentication successful
    #send randCookie and TCP portNumber to client

    return

def AUTH_FAIL ():
    #client authentication fail

    return

#TCP connect
def CONNECTED ():
    #notify client it has been connected

    return

def CHAT_STARTED (sessionID, clientID_B):
    #notify clientA that chat session with clientB has started
    #assign sessionID to the session

    return

def UNREACHABLE (clientID_B):
    #notify clientA clientB is not available for chat

    return

def END_NOTIF (sessionID):
    #notify clients in the session that the session has been terminated

    return

def HISTORY_RES (clientID, message):
    
    return 0
