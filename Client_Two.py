import socket
from MessageObject import MessageObject
import pickle
import threading
import time
import client as cl
import bcrypt
from secrets import token_urlsafe
import hashlib
from aesClass import aesCipher
from utils import messageDict
from time import *

lock = threading.Lock()
chat_timeout = 0
TIMEOUT_VAL = 30
# The message receiving thread
def msgRecv(cipherMachine: aesCipher):
    while True:
        # The receiving TCP socket
        pickedEncMessage = (clSock.Tclient.recv(4096))
        pickedMessage = cipherMachine.decryptMessage(pickedEncMessage)
        message = pickle.loads(pickedMessage)
        global chat_timeout
        if message['messageType'] == 'CHAT_STARTED':
            global msgTargetId
            msgTargetId = message['targetID']
            global sessionID
            sessionID = message['sessionID']
            timer_thread = threading.Thread(target=chatTimeout)
            timer_thread.start()
        elif  message['messageType'] == 'CHAT':
            lock.acquire()
            chat_timeout = 30
            lock.release()
        # Handle object data
        elif message['messageType'] == 'END_NOTIF':
            msgTargetId = -1
            sessionID = -1
            lock.acquire()
            chat_timeout = 0
            lock.release()
        if len(pickedEncMessage) == 0:
            break
        else:
            pass
        print('Message From ', message['senderID'], ': ', message['messageBody'])

# Timeout method
def chatTimeout():
    actualTimeout = False
    lock.acquire()
    global chat_timeout
    chat_timeout = TIMEOUT_VAL
    lock.release()
    while True:
        sleep(1) # Sleep for 1 second 
        lock.acquire()
        chat_timeout = chat_timeout - 1
        actualTimeout = True if chat_timeout == 0 else False
        lock.release()
        if chat_timeout == 0:
            break # Timer ran out, exit function ( Which also end the thread )
        elif chat_timeout == 10:
            print(' \n Chat is disconnecting (Auto Log-off) in 10 seconds, send or recive a message to reset the timer')   
    # End connection with the other Client
    if actualTimeout:
        clSock.END_REQUEST(sessionID, msgTargetId)

# Client Title
print(" CLient 2 ")


var = MessageObject("", -1, "", -1)  # MsgType, senderId, msgBody, targetId
# Create a TCP socket
#clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Create a UDP socket
#udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#udpSocket.connect(('localhost', 6265))

# ====================================================
# The Client TCP section - Mixed for now
# ====================================================
# Send in the id of the client to the server
senderKey = str(200)
senderId = str(222)
msgTargetId = -1
udpConnect = True
reply = None
sessionID = 1000


clSock = cl.clientAPI(int(senderId),int(senderKey))
while True:
    # Initiation Phase
    if udpConnect:
        try:
            if reply == None:
                clSock.HELLO()
                #udpSocket.send(str.encode("HELLO " + str(var.senderId)))
            elif reply != [] and reply[0] == "CHALLENGE":
                salt = reply[1]
                clSock.RESPONSE(senderKey, salt.encode())
                #udpSocket.send(str.encode("RESPONSE " + str(senderKey)))
            elif reply != [] and reply[0]  == "AUTH_FAIL":
                reply = None
                clSock.Uclient.close()
                break
            elif reply != [] and reply[0] == "AUTH_SUCCESS":
                udpConnect = False
                # Make TCP Connection
                clSock.Tclient.connect(('localhost', 6265))
                message = messageDict(senderId, "CONNECT", cookie=randomCookie)
                unencBytes = pickle.dumps(message)
                encMessage = machine.encryptMessage(unencBytes)
                clSock.CONNECT(encMessage)
                print('Sent Connect message')
                # Start the thread to receive message with non blocking type
                threading.Thread(target=msgRecv, args=(machine,)).start()
            if udpConnect:
                # Time out period
                clSock.Uclient.settimeout(5)
                # Retrieve Data
                reply = clSock.Uclient.recv(1024)
                # Check first 2 bits for authentication
                bytes_check = reply[:2]
                if bytes_check == b'as':
                    ck_a = hashlib.pbkdf2_hmac('SHA256', senderKey.encode(), clSock.salt, 100000)
                    machine = aesCipher(ck_a)
                    reply = machine.decryptMessage(reply[2:])
                    reply = reply.decode('utf-8')
                    reply = reply.split()
                    randomCookie = reply[2]
                else:
                    reply = reply.decode('utf-8').split() 
                print(reply)
        except socket.timeout:
            # Assume Packet lost try again
            reply = None
            print("Time Out")
            # udpSocket.close()
            break
    else:
        # CHAT PHASE
        # Ask user for input
        msgInput = input("Client One Msg : \n")

        # If chat message start with the word chat , it indicate that the client is making a chat request to a target
        # client. Currently both clients need to target each other using the chat command
        # chat [target_id_number]

        if msgInput.split()[0] == 'chat':
            # The sender id of this client
            #var.senderId = 222
            # The target id of the client
            #var.targetId = msgInput.split()[1]
            # Set the target id based on the value following the chat keyword
            # chat [target_id_number]
            # Message type so the server set up the target client
            #var.msgType = 'CHATSET'
            #var.msgBody = msgInput
           # dataObject = pickle.dumps(var)
            # Send data to the server
            #clSock.Tclient.send(dataObject)
            msgTargetId = int(msgInput.split()[1])

            clSock.CHAT_REQUEST(int(msgInput.split()[1]))

        # End Chat 
        elif msgInput == 'end chat':

            clSock.END_REQUEST(sessionID, msgTargetId)
            # End Timer 
            '''
            lock.acquire()
            chat_timeout = 0
            lock.release()
            '''
        elif msgInput != 'end client':
            print('---------')

            message = messageDict(senderID=senderId, messageType="CHAT",messageBody=msgInput, targetID=msgTargetId, cookie=randomCookie, sessionID=sessionID)
            unencBytes = pickle.dumps(message)
            encMessage = machine.encryptMessage(unencBytes)
            clSock.CHAT(sessionID,encMessage)
            lock.acquire()
            chat_timeout = 30
            lock.release()
        # Send the command to end server

        else:
            msgInput = 'end server'
            clSock.Tclient.send(bytes(msgInput, 'utf-8'))
            break

# Close socket
clSock.Tclient.close()
