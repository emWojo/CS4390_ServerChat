import socket
from MessageObject import MessageObject
import pickle
import threading
import time

def msgRecv():
    while  True:
        dataClient = (clientSocket.recv(4096))
        # Handle object data
        try:
            # Unpickle data
            dataMsg = pickle.loads(dataClient)
            print('Thread Recv a msg')

            print(str(dataMsg.msgBody) + '\n')
			 # Temporery use talk end command from the other client 
             #to end the read and exit so it does not run in the background
            if dataMsg.msgBody == 'end talk':
                print('Exit thread break')
                break

        # Handle normal data type  data
        except:
            print('except break')
            break






print(" CLient 2 ")
var = MessageObject("", -1, "", -1) # MsgType, senderId, msgBody, targetId

clientSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    udpSocket.connect(('localhost', 6265))
except socket.error as e:
    print(str(e))

# Send in the id
var.msgType = 'HELLO'
var.senderId = 222
senderKey = 200
# Send data to the server
dataObject = pickle.dumps(var)

msgTargetId = -1
udpConnect = True
reply = None
while True:
    #Initiation Phase
    if udpConnect:
        try:
            if reply == None:
                udpSocket.send(str.encode("HELLO "+str(var.senderId)))
            elif reply != [] and reply[0] == "CHALLENGE":
                udpSocket.send(str.encode("RESPONSE "+str(senderKey)))
            elif reply != [] and reply[0] == "AUTH_FAIL":
                reply = None
                udpSocket.close()
                break
            elif reply != [] and reply[0] == "AUTH_SUCCESS":
                udpConnect = False
                # Make TCP Connection
                try:
                    clientSocket.connect(('localhost', 6265))
                except socket.error as e:
                    print(str(e))
                clientSocket.send(dataObject)
                threading.Thread(target=msgRecv).start()
            if udpConnect:
                # Time out period
                udpSocket.settimeout(5)
                reply = udpSocket.recv(1024).decode('utf-8').split()
                print(reply)
        except socket.timeout:
            # Assume Packet lost try again
            reply = None
            print("Time Out")
            #udpSocket.close()
            break
    else:
        # CHAT PHASE
        msgInput = input("Client Two Msg : \n")
        if msgInput.split()[0] == 'chat':
            var.senderId = 222
            var.targetId = msgInput.split()[1]
            msgTargetId  = msgInput.split()[1]
            var.msgType = 'CHATSET'
            var.msgBody = msgInput
            dataObject = pickle.dumps(var)
            # Send data to the server
            clientSocket.send(dataObject)
        elif msgInput != 'end client':
            print('---------')
            var.senderId = 222
            var.msgType = 'MSG'
            var.msgBody = msgInput
            var.targetId = msgTargetId
            dataObject = pickle.dumps(var)
            # Send data to the server
            clientSocket.send(dataObject)


        else:
            msgInput = 'end server'
            clientSocket.send(bytes(msgInput,'utf-8'))
            break
clientSocket.close()
