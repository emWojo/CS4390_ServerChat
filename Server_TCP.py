import socket
import select
import threading
import pickle
import queue
from MessageObject import MessageObject

print("Server Runing")
# Create the server TCP socket
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# serverSocket.set_reuse_addr()
serverSocket.setblocking(False)

try:
    # Binds the TCP socket
    serverSocket.bind(('localhost', 6265))
except socket.error as e:
    print(str(e))
try:
    udpSocket.bind(('localhost', 6265))
except socket.error as e:
    print(str(e))
print(serverSocket)

# UDP
clients = {111: 100, 222: 200, 333: 300}  # temp
addrToId = {}


def udp_thread():
    while True:
        resp = ""
        data, addr = udpSocket.recvfrom(2048)
        print(data, addr)
        data = data.decode('utf-8').split()
        if data[0] == "HELLO":
            if int(data[1]) in clients:
                addrToId[addr] = int(data[1])
                resp = "CHALLENGE " + str(123)
            else:
                # failed challenge
                del addrToId[addr]
        elif data[0] == "RESPONSE":
            if clients[addrToId[addr]] == int(data[1]):
                resp = "AUTH_SUCCESS"
            else:
                del addrToId[addr]
                resp = "AUTH_FAIL"
        udpSocket.sendto(str.encode(resp), addr)
    udpSocket.close()


threading.Thread(target=udp_thread).start()

# ====================================================
# The server TCP section
# ====================================================
# The TCP server will listen to up to 8 connection
# This for the TCP  server socket
serverSocket.listen(8)

# A list that will contain all curently client connected socket
listOfClientSocketOnline = []
# A list that will contain all currently client connected id
listOfClientsOnlineId = []
# A list that will contains all the clients that are currently talking to each other - not used for now
connectedPair = []

# potential_readers , potential_writes, potential_errors that will be passed to the select
# potential_readers is a list of all the sockets that will be ready to read from
potential_readers = [serverSocket]
# potential_writes is a list of all the socket  that will be ready to write to
potential_writes = []
# potential_errors is a lsit that will contain error from handling socket - currently does nothing might be used later
potential_errors = []
# A queue that will hold the message
ClientMessageQueue = {}

# Currently The server will keep on running until it 'end server' command is used by one of the clients
while True:

    # Select function will have potential_readers , potential_writes, potential_errors as parameters where each are
    # lists that will wait until they are ready for reading incoming sockets from client, writing to clients sockets,
    # and errors are received and need to be checked. The select function will provide a multiplexer like behavior to be
    # able send data between clients

    # Can add the UDP socket to the select ?

    # select_ready_to_read, select_ready_to_write, select_error are return result of the select each will contain
    # sockets that are readable, writable and containing errors respectively
    select_ready_to_read, select_ready_to_write, select_error = select.select(potential_readers, potential_writes,
                                                                              potential_errors)

    # For each socket that is received and is in the select_ready_to_read
    for socketTypesRead in select_ready_to_read:

        # Read from the server socket
        if socketTypesRead is serverSocket:
            # Accepts Clients for the Chat Phase
            connectionSocket, connectionAddress = serverSocket.accept()
            print(connectionSocket)
            print(connectionAddress)
            # Prevent connection from blocking
            connectionSocket.setblocking(False)

            # Connection Will each have a queue
            potential_readers.append(connectionSocket)
            # Add the new client to the list of connected clients
            # This list will contain all the clients that have connected client to the server
            listOfClientSocketOnline.append(connectionSocket)
            ClientMessageQueue[connectionSocket] = queue.Queue()

        # Read from the received socket
        else:
            # Can be an object or string
            # Temporarily an object until we can add a diffrent thing ?
            msgObject = socketTypesRead.recv(4096)
            msgObjectDecoded = pickle.loads(msgObject)
            # Print test the decoded object
            print(msgObjectDecoded)

            # Temp for testing - Add to connected client list if the message object type is HELLO
            if msgObjectDecoded.msgType == 'HELLO':
                print("HELLO MsgType")
                # Add the new client id to list
                listOfClientsOnlineId.append(msgObjectDecoded.senderId)
                # Check the client
                print(listOfClientsOnlineId)
                # continue to avoid sending back
                continue
            # Temp for testing - set a chat target for the client if the message object type  is CHATSET
            if msgObjectDecoded.msgType == 'CHATSET':
                print("CHATSET MsgType")
                print("Connect to")

                # Check the client id and the online id list
                print(msgObjectDecoded.targetId)
                print(listOfClientsOnlineId)
                # Assume that target is already online
                # We can add a check if needed here to see if the client is busy ( due to being in a pair already)
                # Can Check also if already connected
                connectedPair.append(tuple((int(msgObjectDecoded.targetId), msgObjectDecoded.senderId)))
                # continue to avoid sending back
                continue
            # Temp for testing - can be used to end threads if this used later
            if msgObjectDecoded.msgBody == 'end talk':
                print(msgObject)
                # can try
                    # close the socket of the ccurrent connection
                    # close the other client socket
                    # break
                    # end client threads
                socketTypesRead.send(bytes("end talk", 'utf-8'))

            # Temp for testing - shut down the server and disconnect the clienst sockets
            if msgObjectDecoded.msgBody == 'end server':
                print(msgObject)
                print(listOfClientSocketOnline)
                # close all socket of the ccurrent connection
                for connectionsOnline in listOfClientSocketOnline:
                    # Inform the clients of the closure
                    connectionsOnline.close()
                # End all clients threads
                # Can also try and end the following :
                    # ClientMessageQueue[connectionSocket] clear the messages ?
                    # end udp thread here later  ?
                # Close the server socket
                serverSocket.close()
                print("Exiting server")
                exit(0)

            # Receiving a message object that is valid
            if msgObject:  # might be none, incorrect
                # added to the queue of the socket
                ClientMessageQueue[socketTypesRead].put(msgObject)
                # If the socket is not in potential_writes to send form later
                if socketTypesRead not in potential_writes:
                    potential_writes.append(socketTypesRead)
            # none msgObject ?
            else:
                # Remove the socket from the potential_writes to avoid
                if socketTypesRead in potential_writes:
                    potential_writes.remove(socketTypesRead)
                potential_readers.remove(socketTypesRead)
                # Close the socket
                socketTypesRead.close()
                # Delete the client socket message
                del ClientMessageQueue[socketTypesRead]

    # For each socket that is writable and is in the select_ready_to_write
    for socketTypesWrite in select_ready_to_write:
        try:
            # get the message from the client messages queue
            msgOn = ClientMessageQueue[socketTypesWrite].get_nowait()
        except queue.Empty:
            # Remove the writable socket
            potential_writes.remove(socketTypesWrite)

        else:
            # Temp - Print the message to test
            print(listOfClientsOnlineId)
            print(int(msgObjectDecoded.targetId))
            print(connectedPair)
            try:
                print(int(msgObjectDecoded.targetId))
                print(int(msgObjectDecoded.senderId))
                print(listOfClientsOnlineId)
                print('=================')
                print(listOfClientsOnlineId.index(int(msgObjectDecoded.targetId)))

                # Send the message to the target client socket

                # This based on using the target client id to find the target client socket in the list and then send
                # the message to it. Currently it depends on using client message object that contain the target id
                # like the TCP message idea of having source and target address
                #
                # make it so only a single chat command start the client chat phase?
                # add the idea of connected pairs to check for error ?
                #
                potential_readers[1 + (listOfClientsOnlineId.index(int(msgObjectDecoded.targetId)))].send(msgOn)
                # Temp - check if the message passed
                print("potential_readers sent")

            # If any error occurs during writing target
            except Exception as e:
                print("Exception e was raised")
                print(e)
