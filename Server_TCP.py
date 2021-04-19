import socket
import select
import threading
import pickle
import queue
from utils import messageDict, sesessionIdGen
from MessageObject import MessageObject
import server as sv
from aesClass import aesCipher

import bcrypt
from secrets import token_urlsafe
import hashlib

from sqlalchemy.orm import sessionmaker
from sqlalchemy import select as sqlSelect
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
from db_define import *

from datetime import datetime

engine = create_engine('sqlite:///DBs/msg.sqlite', echo=False)
connection = engine.connect()
Session = sessionmaker(bind=engine)
session = Session()
#session.query(chat_sess).delete()

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
usrTableResult = session.query(db_usrs).all()

clients = {}

for usr in usrTableResult:
    usrDict = {'password': usr.pwd, 'salt':None, 'saltedPassword':None, 'portNumber': PORT, 'cookie':None}
    clients[int(usr.usr_id)] = usrDict

print(clients)
'''
clients = {
 111: {'password': 100, 'salt':None, 'saltedPassword':None, 'portNumber': PORT, 'cookie':None},
 222: {'password': 200, 'salt':None, 'saltedPassword':None, 'portNumber': PORT, 'cookie':None}, 
 333: {'password': 300, 'salt':None, 'saltedPassword':None, 'portNumber': PORT, 'cookie':None}, 
 444: {'password': 400, 'salt':None, 'saltedPassword':None, 'portNumber': PORT, 'cookie':None}
 }
'''
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
            if DEUBUG_MODE:
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
            if DEUBUG_MODE:
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
                if DEUBUG_MODE:
                    print(id_encBytes)
                id = id_encBytes[:3]
                id = int(id)
                encBytes = id_encBytes[3:]
                if DEUBUG_MODE:
                    print(encBytes)
                machine = sv.createMachine(id, clients)
                decryptedMessage = machine.decryptMessage(encBytes)
                message = pickle.loads(decryptedMessage)
                if DEUBUG_MODE:
                    print(message)

                if message['messageType'] == 'CONNECT':
                    if message['cookie'] == clients[id]['cookie']:
                        connected_client_id = message['senderID']
                        message = messageDict(senderID='Server', messageType='CONNECTED')
                        pickMessage = pickle.dumps(message)
                        encMessage = machine.encryptMessage(pickMessage)
                        sv.CONNECTED(socketTypesRead, encMessage)
                        listOfClientsOnlineId.append(int(connected_client_id))
                    continue
                # Print test the decoded object
                #print(msgObjectDecoded)

                
                # Temp for testing - set a chat target for the client if the message object type  is CHATSET
                if message['messageType']  == 'CHAT_REQUEST':
                    if DEUBUG_MODE:
                        print("CHAT_REQUEST MsgType")
                    # Check the client id and the online id list
                    # Assume that target is already online
                    # We can add a check if needed here to see if the client is busy ( due to being in a pair already) 
                    # Can Check also if already connected
                    isClientOnline = int(message['targetID']) in listOfClientsOnlineId
                    if (isClientOnline):
                        targetClientIdPair = [tupleElem for tupleElem in connectedPair 
                        if tupleElem[0] == int(msgObjectDecoded.targetId)  or tupleElem[1] == int(msgObjectDecoded.targetId)  ]

                        if not targetClientIdPair:

                            connectedPair.append(tuple((int(message['targetID']), int(message['senderID']))))
                            connectionSenderId = message['senderID']
                            connectionTargetId = message['targetID']
                            # Finder chat request sender socket 
                            indexOfSocketId = listOfClientsOnlineId.index(int(connectionSenderId))
                            responeSocket = potential_readers[indexOfSocketId+2] # +2 to account for the already existing sockets
                            #List existing sess ids
                            listExistingSessionIDs = [r.sess_id for r in session.query(chat_sess.sess_id)]
                            SessionID = sesessionIdGen(listExistingSessionIDs)
                            # CHAT_STARTED RES here 
                            sv.CHAT_STARTED(responeSocket,SessionID,connectionTargetId,machine)
                            indexOfSocketId = listOfClientsOnlineId.index(int(connectionTargetId))
                            responeSocket = potential_readers[indexOfSocketId+2]
                            machine2 = sv.createMachine(connectionTargetId, clients)
                            sv.CHAT_STARTED(responeSocket,SessionID,connectionSenderId,machine2)
                            # TODO: Add Session Info To DB
                            sessEntry = chat_sess(sess_id = int(SessionID), usr_id1 = int(connectionSenderId), usr_id2 = int(connectionTargetId))
                            session.add(sessEntry)
                            session.commit()
                        else:
                            # Send a message about client is online but a busy
                            connectionSenderId = message['senderID']
                            connectionTargetId = message['targetID']
                            indexOfSocketId = listOfClientsOnlineId.index(int(connectionSenderId))
                            responeSocket = potential_readers[indexOfSocketId+2]
                            machine = sv.createMachine(connectionSenderId, clients)
                            sv.UNREACHABLE(responeSocket,connectionTargetId, machine)

                            
                    else:
                        #send a message about the client being offline
                        connectionSenderId = message['senderID']
                        connectionTargetId = message['targetID']
                        indexOfSocketId = listOfClientsOnlineId.index(int(connectionSenderId))
                        responeSocket = potential_readers[indexOfSocketId+2]
                        machine = sv.createMachine(connectionSenderId, clients)
                        sv.UNREACHABLE(responeSocket,connectionTargetId, machine)
                    # continue to avoid sending back
                    continue
                # Temp for testing - can be used to end threads if this used later
                if message['messageType'] == 'END_REQUEST':
                    print(message)
                    connectionSenderId = message['senderID']
                    connectionTargetId = message['targetID']
                    SessionID = 1000
                    # Send disconnected Notifcation message 
                    # The sender 
                    indexOfSocketId = listOfClientsOnlineId.index(int(connectionSenderId))
                    responeSocket = potential_readers[indexOfSocketId+2] # +2 to account for the already existing sockets
                    machine = sv.createMachine(connectionSenderId, clients)
                    sv.END_NOTIF(responeSocket, SessionID,machine)
                    # The target
                    indexOfSocketId = listOfClientsOnlineId.index(int(connectionTargetId))
                    responeSocket = potential_readers[indexOfSocketId+2] # +2 to account for the already existing sockets
                    machine2 = sv.createMachine(connectionTargetId, clients)
                    sv.END_NOTIF(responeSocket, SessionID,machine2)

                    # SessionID from the sessionIDList ( If we make one )
                    #TODO Remove session id 

                    # Find the target pair from the  connectedPair list
                    targetClientIdPair = [tupleElem for tupleElem in connectedPair if tupleElem[0] == int(connectionSenderId) or tupleElem[1] == int(connectionSenderId)]
                    if DEUBUG_MODE:
                        print("targ")
                        print(targetClientIdPair)
                        print("con")
                        print(connectedPair)
                    # Remove from the list
                    if targetClientIdPair:
                        connectedPair.remove(targetClientIdPair[0])                    
                    continue

                # Temp for testing - shut down the server and disconnect the clienst sockets
                if message['messageType'] == 'End Server':
                    print(message)
                    if DEUBUG_MODE:
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
                if message['messageBody']:  # might be none 
                    # added to the queue of the socket
                    outGoingMessage = messageDict(senderID=int(message['senderID']), 
                    targetID=int(message['targetID']),  
                    messageType='CHAT',
                    messageBody=message['messageBody'],
                    sessionID=message['sessionID'],
                    port=PORT)
                    ClientMessageQueue[socketTypesRead].put(outGoingMessage)
                    # TODO: Add message to DB
                    msgEntry = msgs(sess_id=int(message['sessionID']), time=datetime.now(), sender_id=int(message['senderID']), msg_body=message['messageBody'] )
                    session.add(msgEntry)
                    session.commit()

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

                try:

                    if DEUBUG_MODE:
                        print(listOfClientsOnlineId)
                        print('=================')

                    # Send the message to the target client socket

                    # This based on using the target client id to find the target client socket in the list and then send
                    # the message to it. Currently it depends on using client message object that contain the target id
                    # like the TCP message idea of having source and target address
                    #
                    #
                    try:
                        idTarget = [tupleElem for tupleElem in connectedPair if tupleElem[0]== int(msgOn['senderID']) or tupleElem[1] == int(msgOn['senderID'])]
                        print(connectedPair)
                        if idTarget[0][1] == int(msgOn['senderID'])  :
                            targetClient = listOfClientsOnlineId.index(int(idTarget[0][0]))
                        else:
                            targetClient = listOfClientsOnlineId.index(int(idTarget[0][1]))
                        msgTargetIndex = 2 + targetClient # + 2 to account for the UDP and TCP socket in the lsit 
                        targetID = int(msgOn['targetID'])
                        machine3 = sv.createMachine(targetID, clients)
                        pickMessage = pickle.dumps(msgOn)
                        encMessage = machine3.encryptMessage(pickMessage)
                        totMessage = encMessage
                        potential_readers[msgTargetIndex].send(totMessage) 
                        # Temp - check if the message passed
                        if DEUBUG_MODE:
                            print("potential_readers sent")
                    except Exception as e:
                        if DEUBUG_MODE:
                            print("Exception: ", str(e), " was raised First")
                # If any error occurs during writing target
                except Exception as e:
                    if DEUBUG_MODE:

                                    print("Exception: ", str(e), " was raised Second")
