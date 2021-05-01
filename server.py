import socket
import bcrypt
import pickle
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

def CHAT_STARTED (socket, sessionID, clientID_B, machine):
    #notify clientA that chat session with clientB has started
    #assign sessionID to the session
    msgOn = 'Connected To Client B wiht the id [ '+ str(clientID_B) +' ]' 
    message = messageDict(senderID='Server', targetID=(int(clientID_B)), sessionID=sessionID,messageType='CHAT_STARTED',messageBody=msgOn)
    pickleMessage = pickle.dumps(message)
    encMessage = machine.encryptMessage(pickleMessage) 
    socket.send(encMessage)   

def UNREACHABLE (socket, clientID_B,machine):
    #notify clientA clientB is not available for chat
    msgOn = 'Client B wiht the id [ '+ str(clientID_B) +' ] Is unreachable' 
    message = messageDict(senderID='Server', targetID=(int(clientID_B)),messageType='UNREACHABLE',messageBody=msgOn)
    pickleMessage = pickle.dumps(message)
    encMessage = machine.encryptMessage(pickleMessage) 
    socket.send(encMessage)   

def END_NOTIF (socket, sessionID, machine):
    #notify clients in the session that the session has been terminated
    msgOn = 'session [ '+ str(sessionID) +' ] has been terminted' 
    message = messageDict(senderID='Server', sessionID=sessionID ,messageType='END_NOTIF',messageBody=msgOn)
    pickleMessage = pickle.dumps(message)
    encMessage = machine.encryptMessage(pickleMessage) 
    socket.send(encMessage)   

def HISTORY_RES (socket, history, machine):
    """
    historyStr = []
    for msg in history:
        historyStr.append(str(msg.sess_id)+" from: "+str(msg.sender_id)+"  "+str(msg.msg_body))
    """
    message = messageDict(senderID='Server', messageType='HISTORY_RES', messageBody=history)
    pickleMessage = pickle.dumps(message)
    encMessage = machine.encryptMessage(pickleMessage) 
    socket.send(encMessage)

def LOG_OFF(socket, machine):
    message = messageDict(senderID='Server', messageType='LOG_OFF')
    pickleMessage = pickle.dumps(message)
    encMessage = machine.encryptMessage(pickleMessage) 
    socket.send(encMessage)

##Helper Functions
def createMachine(connectionSenderId, clients):
    clientKey = clients[connectionSenderId]['password']
    salt = clients[connectionSenderId]['salt']
    ck_a = hashlib.pbkdf2_hmac('SHA256', str(clientKey).encode(), salt, 100000)
    machine = aesCipher(ck_a)
    return machine 

def disconnectMsg(message, clients, potential_readers, listOfClientsOnlineId):
    connectionSenderId = message['senderID']
    connectionTargetId = message['targetID']
    SessionID = message['sessionID']
    # Send disconnected Notifcation message 
    # The sender 
    indexOfSocketId = listOfClientsOnlineId.index(int(connectionSenderId))
    responseSocket = potential_readers[indexOfSocketId+2] # +2 to account for the already existing sockets
    machine = createMachine(connectionSenderId, clients)
    END_NOTIF(responseSocket, SessionID, machine)
    # The target
    if int(connectionTargetId) > 0:
        indexOfSocketId = listOfClientsOnlineId.index(int(connectionTargetId))
        responseSocket = potential_readers[indexOfSocketId+2] # +2 to account for the already existing sockets
        machine2 = createMachine(connectionTargetId, clients)
        END_NOTIF(responseSocket, SessionID, machine2)




                            