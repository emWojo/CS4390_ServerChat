import socket
import select
import threading
import pickle
import queue
from utils import messageDict
from MessageObject import MessageObject
import server as sv
from aesClass import aesCipher

import bcrypt
from secrets import token_urlsafe
import hashlib

HOST = 'localhost'
PORT = 6265
DEUBUG_MODE = False

print("Server Runing")
# Create the server TCP socket 
tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# serverSocket.set_reuse_addr()
tcpSocket.setblocking(False)

try:
    # Binds the TCP socket
    tcpSocket.bind(('localhost', 6265))
except socket.error as e:
    print(str(e))


try:
    udpSocket.bind(('localhost', 6265))
except socket.error as e:
    print(str(e))

if DEUBUG_MODE:
    print(tcpSocket)

# UDP

clients = {
 111: {'password': 100, 'salt':None, 'saltedPassword':None, 'portNumber': PORT, 'cookie':None},
 222: {'password': 200, 'salt':None, 'saltedPassword':None, 'portNumber': PORT, 'cookie':None}, 
 333: {'password': 300, 'salt':None, 'saltedPassword':None, 'portNumber': PORT, 'cookie':None}, 
 444: {'password': 400, 'salt':None, 'saltedPassword':None, 'portNumber': PORT, 'cookie':None}
 }
# TODO: get rid of this since clientID will be in dict
addrToId = {}




# ====================================================
# The server TCP section
# ====================================================
# The TCP server will listen to up to 8 connection
# This for the TCP  server socket
tcpSocket.listen(8)

# A list that will contain all curently client connected socket
listOfClientSocketOnline = []
# A list that will contain all currently client connected id
listOfClientsOnlineId = []
# A list that will contains all the clients that are currently talking to each other - not used for now
connectedPair = []

# potential_readers , potential_writes, potential_errors that will be passed to the select
# potential_readers is a list of all the sockets that will be ready to read from
potential_readers = [tcpSocket, udpSocket]
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

    # select_ready_to_read, select_ready_to_write, select_error are return result of the select each will contain
    # sockets that are readable, writable and containing errors respectively
    select_ready_to_read, select_ready_to_write, select_error = select.select(potential_readers, potential_writes,
                                                                              potential_errors)

    # For each socket that is received and is in the select_ready_to_read
    for socketTypesRead in select_ready_to_read:
        print(socketTypesRead)
        if socketTypesRead is udpSocket:
            resp = ""
            data, addr = udpSocket.recvfrom(2048)
            print(data, addr)
            data = data.decode('utf-8').split()
            message = ""

            if data[0] == "HELLO":
                if int(data[1]) in clients:
                    clientID = int(data[1])
                    addrToId[addr] = clientID
                    password = clients[clientID]['password']
                    salt = clients[clientID]['salt'] = bcrypt.gensalt()
                    clients[clientID]['saltedPassword'] = bcrypt.hashpw(str(password).encode(), salt)
                    sv.CHALLENGE(udpSocket, clientID, addr, salt)
                else:
                    # failed challenge
                    #del addrToId[addr]
                    pass
            elif data[0] == "RESPONSE":
                clientID = addrToId[addr]
                del addrToId[addr] 
                saltyPassword = data[1]
                if DEUBUG_MODE:
                    print(clients[clientID]['saltedPassword'])
                    print(saltyPassword)

                if clients[clientID]['saltedPassword'] == saltyPassword.encode():
                    cookie = clients[clientID]['cookie'] = token_urlsafe(16)
                    password = clients[clientID]['password']
                    salt = clients[clientID]['salt']
                    sv.AUTH_SUCCESS(udpSocket, clientID, addr, cookie, str(password), salt, PORT)       
                else:
                    sv.AUTH_FAIL(udpSocket, clientID, addr)
 
            # Udp would not need to be added to the socket list or have a message queue
        # Read from the server socket
        if socketTypesRead is tcpSocket:
            #Preconnect Message Read
            connectionSocket, connectionAddress = tcpSocket.accept()
            print(connectionSocket)
            print(connectionAddress)
            # Check if the connection cookie is valid 
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
            if socketTypesRead is not udpSocket:
                
                # Can be an object or string
                # Temporarily an object until we can add a diffrent thing ?
                #msgObject = socketTypesRead.recv(4096)
                #msgObjectDecoded = pickle.loads(msgObject)
                msgObjectDecoded = None
                id_encBytes = socketTypesRead.recv(4096)
                print(id_encBytes)
                id = id_encBytes[:3]
                id = int(id)
                encBytes = id_encBytes[3:]
                print(encBytes)
                ck_a = hashlib.pbkdf2_hmac('SHA256', str(clients[int(id)]['password']).encode(), clients[int(id)]['salt'], 100000)
                machine = aesCipher(ck_a)
                decryptedMessage = machine.decryptMessage(encBytes)
                message = pickle.loads(decryptedMessage)
                print(message)

                if message['messageType'] == 'CONNECT':
                    if message['cookie'] == clients[id]['cookie']:
                        message = messageDict(senderID='Server', messageType='CONNECTED')
                        pickMessage = pickle.dumps(message)
                        encMessage = machine.encryptMessage(pickMessage)
                        sv.CONNECTED(socketTypesRead, encMessage)

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
                    isClientOnline = int(msgObjectDecoded.targetId) in listOfClientsOnlineId
                    if (isClientOnline):
                        targetClientIdPair = [tupleElem for tupleElem in connectedPair 
                        if tupleElem[0] == int(msgObjectDecoded.targetId)  or tupleElem[1] == int(msgObjectDecoded.targetId)  ]

                        if not targetClientIdPair:
                            connectedPair.append(tuple((int(msgObjectDecoded.targetId), msgObjectDecoded.senderId)))
                        else:
                            #TODO: Send a message about client is online but a busy
                            pass 
                    else:
                        #TODO: send a message about the client being offline 
                        pass
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
                    tcpSocket.close()
                    udpSocket.close()
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
        if socketTypesWrite is not udpSocket:

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
                    try:
                        idTarget = [tupleElem for tupleElme in connectedPair
                        if tupleElem[0]== msgObjectDecoded.senderId or tupleElem[1] == msgObjectDecoded.senderId]

                        if idTarget[0][1] == msgObjectDecoded.senderId :
                            targetClient = listOfClientsOnlineId.index(int(idTarget[0][0]))
                            msgTargetIndex = 2 + targetClient # + 2 to account for the UDP and TCP socket in the lsit 
                            potential_readers[msgTargetIndex].send(msgOn)
                        else:
                            targetClient = listOfClientsOnlineId.index(int(idTarget[0][1]))
                            msgTargetIndex = 2 + targetClient # + 2 to account for the UDP and TCP socket in the lsit 
                            potential_readers[msgTargetIndex].send(msgOn)
                        # Temp - check if the message passed
                        print("potential_readers sent")
                    except Exception as e:
                        print("Exception: ", e, " was raised")


                # If any error occurs during writing target
                except Exception as e:
                    print("Exception: ", e, " was raised")
