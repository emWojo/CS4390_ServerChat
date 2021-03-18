import socket
from MessageObject import MessageObject
import pickle
import threading
import time


# The message receiving thread
def msgRecv():
    while True:
        # The receiving TCP socket
        dataClient = (clientSocket.recv(4096))
        # Handle object data
        try:
            # Unpickle data - convert the object byte stream to object
            dataMsg = pickle.loads(dataClient)
            print('Thread Recv a msg')

            print(str(dataMsg.msgBody) + '\n')
            # Temporaryly will use 'talk end' command from the other client
            # to end the read and exit so it does not run in the background
            if dataMsg.msgBody == 'end talk':
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
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Create a UDP socket
udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    udpSocket.connect(('localhost', 6265))
except socket.error as e:
    print(str(e))

# ====================================================
# The Client TCP section - Mixed for now
# ====================================================
# Send in the id of the client to the server
var.msgType = 'HELLO'
var.senderId = 111
senderKey = 100
# Pickle convert the object into a byte stream
dataObject = pickle.dumps(var)

msgTargetId = -1
udpConnect = True
reply = None

while True:
    # Initiation Phase
    if udpConnect:
        try:
            if reply == None:
                udpSocket.send(str.encode("HELLO " + str(var.senderId)))
            elif reply != [] and reply[0] == "CHALLENGE":
                udpSocket.send(str.encode("RESPONSE " + str(senderKey)))
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
                # Start the thread to receive message with non blocking type
                threading.Thread(target=msgRecv).start()
            if udpConnect:
                # Time out period
                udpSocket.settimeout(5)
                # Retrieve Data
                reply = udpSocket.recv(1024).decode('utf-8').split()
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
            clientSocket.send(dataObject)

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
            clientSocket.send(dataObject)

        # Send the command to end server
        else:
            msgInput = 'end server'
            clientSocket.send(bytes(msgInput, 'utf-8'))
            break

# Close socket
clientSocket.close()
