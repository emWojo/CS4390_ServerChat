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
            print(' Thread Recv')

            print(str(dataMsg.msgBody) + '\n')
			 # Temporery use talk end command from the other client to end the read and exit so it does not run in the background

            if dataMsg.msgBody == 'end talk':
                print('Exit Thread')
                break

        # Handle normal data type  data
        except:
            #appWindow.setTextArea('TextAreaScroll', str(data.decode()) + '\n')
            print('except')
            #print(str(dataClient.decode()) + '\n')
            break






print(" CLient 4 ")
var = MessageObject("", -1, "", -1) # MsgType, senderId, msgBody, targetId

clientSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
# serverSocket.setblocking(False)
clientSocket.connect(('localhost', 6265))

#msg = clientSocket.recv(4096)
# Send in the id
#clientSocket.send(bytes(444,'utf-8'))
var.msgType = 'HELLO'
var.senderId = 444
#dataStr = pickle.dumps(var)
# Send data to the server
#socketServOne.send(dataStr)
dataObject = pickle.dumps(var)
# Send data to the server
clientSocket.send(dataObject)
#serverConnectionMsg = clientSocket.recv(4096)
#print(serverConnectionMsg)

threading.Thread(target=msgRecv).start()
msgTargetId = -1
while True:
    msgInput = input("Client One Msg : \n")
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

        #clientSocket.send(bytes(msgInput,'utf-8'))
        dataObject = pickle.dumps(var)
        # Send data to the server
        clientSocket.send(dataObject)

        # check if not object as server send plain msg on exit
        #msgObject = clientSocket.recv(4096)
        #msgObjectDecoded = pickle.loads(msgObject)

        #decodeMsg = msg.decode('utf-8')
        #print(msgObjectDecoded.msgBody)

        #clientSocket.send(bytes(msg,"utf-8"))
        #print(msg.decode("utf-8"))

    else:
        msgInput = 'end server'
        clientSocket.send(bytes(msgInput,'utf-8'))
        break
clientSocket.close()
