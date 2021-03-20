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


# The message receiving thread
def msgRecv(cipherMachine: aesCipher):
    while True:
        # The receiving TCP socket
        pickedEncMessage = (clSock.Tclient.recv(4096))
        # Handle object data
        try:
            # Unpickle data - convert the object byte stream to object
            pickedMessage = cipherMachine.decryptMessage(pickedEncMessage)
            message = pickle.loads(pickedMessage)
            print('Thread Recv a msg')
            print(message)

            # Temporaryly will use 'talk end' command from the other client
            # to end the read and exit so it does not run in the background
            if message['messageType'] == 'end talk':
                print('Exit thread break')
                break

        # Handle normal data type  data - this will used to exit the client once the server shutdown
        except:
            print('Except break')
            break


# Client Title
print(" CLient 1 ")


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
senderKey = str(100)
senderId = str(111)
msgTargetId = -1
udpConnect = True
reply = None

clSock = cl.clientAPI(int(senderId))
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
            var.senderId = 111
            # The target id of the client
            var.targetId = msgInput.split()[1]
            # Set the target id based on the value following the chat keyword
            # chat [target_id_number]
            msgTargetId = msgInput.split()[1]
            # Message type so the server set up the target client
            var.msgType = 'CHATSET'
            var.msgBody = msgInput
            dataObject = pickle.dumps(var)
            # Send data to the server
            clSock.Tclient.send(dataObject)

        # Temp test msg - 'end client' could be used is temp place holder to end thread
        # but 'end talk' will be used to end the client
        elif msgInput != 'end client':
            print('---------')
            # Set the object data fields
            # client sender id
            var.senderId = 111
            # message type
            var.msgType = 'MSG'
            # message body that based on user input
            var.msgBody = msgInput
            # the target id which is based on using chat [target_id_number] command beforehand
            var.targetId = msgTargetId
            # Pickle convert the object into a byte stream
            dataObject = pickle.dumps(var)
            # Send data to the server
            clSock.Tclient.send(dataObject)

        # Send the command to end server
        else:
            msgInput = 'end server'
            clSock.Tclient.send(bytes(msgInput, 'utf-8'))
            break

# Close socket
clSock.Tclient.close()
