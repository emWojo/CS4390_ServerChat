import pickle
import socket
import select
import queue

from CustomExceptions import ClientIsBusy, ClientIsNotOnline, ClinetIsAlreadyConnected

# This method is used to check if a connection exists between the pairs
def checkConnectionTarget(target):
    if len(connectedPairs) == 0:
        return False
    for pair in connectedPairs:
        if pair[1] == target:
            return True  # if true then it is busy
    return False  # then it free

# This method is used to check if a connection exists between the pairs and return the pair index if so
def isClientBusy(target):
    if len(connectedPairs) == 0:
        return False
    for eachPair in connectedPairs:
        if eachPair[0] == target:
            return eachPair[1]



# Server socket setup
socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Set the server socket to be a nonblocking socket
socketServer.setblocking(False)
socketServer.bind(('localhost', 6565))
# The number of clients that will be allowed to connect
socketServer.listen(10)
# Inform the user the server is running
print("Server is Running")

# List
# Currently Connected
readInput = [socketServer]
writeOutput = []
messageOutputQueue = {}

# The list and variables are initialized with dummy elements to server as sentinel value
# This list will hold the id of all the currently connected clients
connectedClientsId = [0]
connectedClientsTarget = -1
connectedClientsCurrent = -1
# This list of pairs will be used to check which clients are busy talking with each other
connectedPairs = [(0, 0)]
# The sever will keep running until it is manually stopped or crashes
while True:


    read, write, error = select.select(readInput, writeOutput, readInput)
    # Handle reading socket from client
    for socketType in read:
        if socketType is socketServer:
            connection, address = socketType.accept()
            # Connection received
            print("Connection from " + str(address) + "address")
            # Set the connection itself to be non-blocking
            connection.setblocking(False)

            # Add the conection to the to read from list
            readInput.append(connection)

            # Buffer the messages
            messageOutputQueue[connection] = queue.Queue()
        else:
            # Recive data from the the clients
            data = socketType.recv(2048)
            # Unpikle data to extra object variable. The server should still be able to handle reciving other types,
            # some modifcation could be applied in the code block
            dataObject = pickle.loads(data)

            # Check the message type
            # This should be a temporery place holder until we add protocols
            # Message type "HELLO" will be sent by the client when it first run
            if dataObject.MsgType == "HELLO":
                # Add the client to online client list connectedClientsId
                connectedClientsId.append(int(dataObject.senderId))
                print("HELLO")
                print(int(dataObject.senderId))

            # Attempt to Establish a connection with the target client
            # This should be a temporery place holder until we add protocols
            # Message type "CHAT_REQUEST" will be sent by the client when they want to chat with the target client
            # chat [target_id]
            elif dataObject.MsgType == "CHAT_REQUEST" and dataObject.msgBody.split()[0].lower() == "chat":

                try:
                    # Check if the requested client is online
                    # by checking connectedClientsId list
                    if (int(dataObject.targetId) in connectedClientsId):
                        try:
                            # check if already connected
                            if checkConnectionTarget(connectedClientsId.index(int(dataObject.targetId))) == False:

                                # Find the position of the clients in connectedClientsId
                                connectedClientsTarget = connectedClientsId.index(int(dataObject.targetId))
                                connectedClientsCurrent = connectedClientsId.index(int(dataObject.senderId))

                                # Use the connectedClientsId postion to add a new connection to the list
                                connectedPairs.append(tuple((connectedClientsCurrent, connectedClientsTarget)))
                                connectedPairs.append(tuple((connectedClientsTarget, connectedClientsCurrent)))
                                # Inform both clients that they are connected
                                # This should be a temporery place holder until we add protocols
                                connect_msg = "Connected to client " + str(dataObject.targetId)
                                connect_msgByte = bytes(connect_msg, 'utf-8')
                                readInput[connectedClientsId.index(int(dataObject.senderId))].send(connect_msgByte)
                                connect_msg = "Connected to client " + str(dataObject.senderId)
                                connect_msgByte = bytes(connect_msg, 'utf-8')
                                readInput[connectedClientsId.index(int(dataObject.targetId))].send(connect_msgByte)
                            else:
                                # If the client is already in a pair with another client , then reject the connection
                                # and trow ClientIsBusy exception
                                raise ClientIsBusy
                        except ClientIsBusy:
                            # This should be a temporery place holder until we add protocols
                            busyMsg = "Client   " + str(dataObject.targetId) + " is busy"
                            busyMsgByte = bytes(busyMsg, 'utf-8')
                            readInput[connectedClientsId.index(int(dataObject.senderId))].send(busyMsgByte)
                    else:
                        # If the client is not online , then reject the connection
                        # and trow ClientIsNotOnline exception
                        raise ClientIsNotOnline
                except ClientIsNotOnline:
                    # This should be a temporery place holder until we add protocols
                    busyMsg = "Client   " + str(dataObject.targetId) + " is not online"
                    busyMsgByte = bytes(busyMsg, 'utf-8')
                    readInput[connectedClientsId.index(int(dataObject.senderId))].send(busyMsgByte)




            # Process a chat message
            else:

                if data:
                    messageOutputQueue[socketType].put(data)
                    if socketType not in writeOutput:
                        writeOutput.append(socketType)
                else:
                    if socketType in writeOutput:
                        writeOutput.remove(socketType)
                    readInput.remove(socketType)
                    socketType.close()
                    del messageOutputQueue[socketType]

    # Handle writing socket to client

    for socketType in write:
        try:
            next_msg = messageOutputQueue[socketType].get_nowait()
        except queue.Empty:
            writeOutput.remove(socketType)
        else:

            try:
                # Before sending any messages the server will check if the message pair been intilized and the socket type
                # matched
                if (readInput[connectedClientsCurrent] == socketType) and (connectedClientsTarget != -1) :

                    readInput[connectedClientsId.index(int(dataObject.targetId))].send(next_msg)
                elif connectedClientsCurrent != -1 :
                    # Find if the sender and  target are a valid pair
                    if isClientBusy(connectedClientsId.index(int(dataObject.senderId))) != None:
                        readInput[isClientBusy(connectedClientsId.index(int(dataObject.senderId)))].send(next_msg)

                else:
                    print("ValueError")
                    raise ValueError



            except  ValueError:
                busyMsg = 'TEMP msg - Switched message to invalid client during chat ? Make sure target client is connected ?'
                busyMsgByte = bytes(busyMsg, 'utf-8')
                readInput[connectedClientsId.index(int(dataObject.senderId))].send(busyMsgByte)
