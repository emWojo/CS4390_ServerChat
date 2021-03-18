import socket
from MessageObject import MessageObject
import pickle
import threading

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






print(" CLient 4 ")
var = MessageObject("", -1, "", -1) # MsgType, senderId, msgBody, targetId

clientSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
clientSocket.connect(('localhost', 6265))

# Send in the id
var.msgType = 'HELLO'
var.senderId = 444
# Send data to the server
dataObject = pickle.dumps(var)
# Send data to the server
clientSocket.send(dataObject)

threading.Thread(target=msgRecv).start()
msgTargetId = -1
while True:
    msgInput = input("Client Four Msg : \n")
    if msgInput.split()[0] == 'chat':
        var.senderId = 444
        var.targetId = msgInput.split()[1]
        msgTargetId  = msgInput.split()[1]

        var.msgType = 'CHATSET'
        var.msgBody = msgInput
        dataObject = pickle.dumps(var)
        # Send data to the server
        clientSocket.send(dataObject)
    elif msgInput != 'end client':
        print('---------')
        var.senderId = 444
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
