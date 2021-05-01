import socket
import pickle
import threading
import time
import readline
import sys
import client as cl
import bcrypt
from secrets import token_urlsafe
import hashlib
from aesClass import aesCipher
import utils
from utils import TIMEOUT_VAL
from time import *
from db_define import *


lock = threading.Lock()
RECVIN = True

# Send in the id of the client to the server
senderKey = str(800)
senderId = str(888)
msgTargetId = -1
# 0-not logged on, 1-connect phase, 2-chat phase
connectType = 0
reply = None
sessionID = 1000
recvThread = None
chat_timeout = TIMEOUT_VAL

# The message receiving thread
def msgRecv(cipherMachine: aesCipher):
    #callsToDecrypt = 0
    while RECVIN:
        # The receiving TCP socket
        global chat_timeout
        pickedEncMessage = clSock.Tclient.recv(65536)
        #callsToDecrypt+=1
        #print("This is call number", callsToDecrypt, "to decrypt.")
        pickedMessage = cipherMachine.decryptMessage(pickedEncMessage)
        message = pickle.loads(pickedMessage)
        if message['messageType'] == 'CHAT_STARTED':
            global msgTargetId
            msgTargetId = message['targetID']
            global sessionID
            sessionID = message['sessionID']
            timer_thread = threading.Thread(target=chatTimeout)
            timer_thread.start()
        elif  message['messageType'] == 'CHAT':
            lock.acquire()
            #print(chat_timeout)
            chat_timeout = TIMEOUT_VAL
            lock.release()
        elif message['messageType'] == 'HISTORY_RES':
            lock.acquire()
            #print(chat_timeout)
            chat_timeout = TIMEOUT_VAL
            lock.release()
            if len(message['messageBody']) > 0:
                for msg in message['messageBody']:
                    print(msg.sess_id, "from:", msg.sender_id, " ", msg.msg_body)
            else:
                print('No History Found.')
            message['messageBody'] = 'History Printed.'
        
        elif message['messageType'] == 'END_NOTIF':
            msgTargetId = -1
            sessionID = -1
            lock.acquire()
            chat_timeout = 0
            lock.release()

        elif message['messageType'] == 'LOG_OFF':
            clSock.Tclient.close()
            clSock.Tclient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            lock.acquire()
            chat_timeout = 0
            lock.release()
            sleep(2)
            #print(timer_thread.is_alive())
            sys.exit()
            break
        
        # Handle object data
        if len(pickedEncMessage) == 0:
            break
        else:
            msg = 'Message From ' + str(message['senderID']) + ': ' + (message['messageBody'] if message['messageBody'] is not None else 'None')
            sys.stdout.write("\r" + '------------\n')
            print(msg)
            sys.stdout.flush()
            # Get the current line buffer and reprint it, in case some input had started to be entered when the prompt was switched
            print('------------')
            print('Your msg: ', end='')
            sys.stdout.write(readline.get_line_buffer())
            sys.stdout.flush()
            


def keepAlive():

    while True:
        sleep(1)
        clSock.KEEP_ALIVE()

# Timeout method
def chatTimeout():
    actualTimeout = False
    lock.acquire()
    global chat_timeout
    chat_timeout = TIMEOUT_VAL
    lock.release()
    while RECVIN:
        sleep(1) # Sleep for 1 second 
        lock.acquire()
        chat_timeout = chat_timeout - 1
        actualTimeout = True if chat_timeout == 0 else False
        lock.release()
        if chat_timeout <= 0:
            break # Timer ran out, exit function ( Which also end the thread )
        elif chat_timeout == 10:
            msg = 'Chat is disconnecting (Auto Log-off) in 10 seconds, send or recive a message to reset the timer'
            sys.stdout.write("\r" + '------------\n')
            print(msg)
            sys.stdout.flush()
            # Get the current line buffer and reprint it, in case some input had started to be entered when the prompt was switched
            print('------------')
            print('Your msg: ', end='')
            sys.stdout.write(readline.get_line_buffer())
            sys.stdout.flush()   
    # End connection with the other Client
    if actualTimeout:
        clSock.END_REQUEST(sessionID, msgTargetId)

# Client Title
print(" CLient 2 ")


# Create a TCP socket
#clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Create a UDP socket
#udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#udpSocket.connect(('localhost', 6265))

# ====================================================
# The Client TCP section - Mixed for now
# ====================================================

# We are passing sender id  and sender key to the clientAPI 
clSock = cl.clientAPI(int(senderId),int(senderKey))
while True:
    # Initiation Phase
    if connectType == 0:
        #TODO: Wait for log on message
        #print(threading.enumerate())
        print("Type 'logon' to start connection  or 'exit' to shut the app")
        ins = input()
        if ins == "logon":
            connectType = 1
        elif ins == "exit":
            utils.screenClear()
            exit()
        else:
            print('Invalid input.')
    # Connect Phase
    elif connectType == 1:
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
                connectType = 2
                # Make TCP Connection
                clSock.Tclient.connect(('localhost', 6265))
                message = utils.messageDict(senderId, "CONNECT", cookie=randomCookie)
                unencBytes = pickle.dumps(message)
                encMessage = machine.encryptMessage(unencBytes)
                clSock.CONNECT(encMessage)
                print('Sent Connect message')
                # Start the thread to receive message with non blocking type
                recvThread = threading.Thread(target=msgRecv, args=(machine,))
                recvThread.start()
                #threading.Thread(target=keepAlive).start()
            if connectType == 1:
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
        msgInput = input("Your Msg: ")

        # If chat message start with the word chat , it indicate that the client is making a chat request to a target
        # client. Currently both clients need to target each other using the chat command
        # chat [target_id_number]

        if msgInput.split()[0] == 'chat':
            # The sender id of this client
            #var.senderId = 111
            # The target id of the client
            #var.targetId = msgInput.split()[1]
            # Set the target id based on the value following the chat keyword
            # chat [target_id_number]
            #msgTargetId = msgInput.split()[1]
            # Message type so the server set up the target client
            #var.msgType = 'CHATSET'
            #var.msgBody = msgInput
           # dataObject = pickle.dumps(var)
            # Send data to the server
            #clSock.Tclient.send(dataObject)
            msgTargetId = int(msgInput.split()[1])
            clSock.CHAT_REQUEST(int(msgInput.split()[1]))
        # Get Chat History
        elif msgInput.split()[0] == 'history':
            clSock.HISTORY_REQ(int(msgInput.split()[1]))
        # End Chat 
        elif msgInput == 'end chat':
            clSock.END_REQUEST(sessionID, msgTargetId)
            # End Timer 
            '''
            lock.acquire()
            chat_timeout = 0
            lock.release()
            '''
        elif msgInput == "logoff":
            #Tell server logging off
            #Stop receiving messages
            #recvThread.join()
            #Tear down TCP connection
            clSock.LOG_OFF(msgTargetId, sessionID)
            connectType = 0

        elif msgInput != 'end client':
            print('------------')

            message = utils.messageDict(senderID=senderId, messageType="CHAT",messageBody=msgInput, targetID=msgTargetId, cookie=randomCookie, sessionID=sessionID)
            unencBytes = pickle.dumps(message)
            encMessage = machine.encryptMessage(unencBytes)
            clSock.CHAT(sessionID,encMessage)
            lock.acquire()
            chat_timeout = TIMEOUT_VAL
            lock.release()
        # Send the command to end server
        else:
            msgInput = 'end server'
            clSock.Tclient.send(bytes(msgInput, 'utf-8'))
            break

# Close socket
clSock.Tclient.close()