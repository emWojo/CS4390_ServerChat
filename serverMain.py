import secrets
import bcrypt, hashlib, queue, pickle, select, socket, threading
import server as sv

from aesClass import aesCipher
from datetime import datetime
from db_define import *
from secrets import token_urlsafe
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select as sqlSelect
from sqlalchemy.ext.declarative import declarative_base
from utils import messageDict, sesessionIdGen

Base = declarative_base()

# Create DB interface
engine = create_engine('sqlite:///DBs/msg.sqlite', echo=False)
connection = engine.connect()
Session = sessionmaker(bind=engine)
session = Session()

# Define connection information
HOST = 'localhost'
PORTS = [6265]
PORT = None
DEBUG_MODE = False


if __name__ == '__main__':
    print("Server Runing")
    # Create the server TCP socket 
    tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpSocket.setblocking(False)
    # Create the server UDP socket 
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Import users table from database
    usrTableResult = session.query(db_usrs).all()
    # The clients database will be convereted to a dictionary and stored in this
    clients = {}
    # A mapping of client IDs to addresses
    addrToId = {}
    tcpNotBound = True
    udpNotBound = True

    # A list that will contain all client sockets curently connected
    listOfClientSocketOnline = []
    # A list that will contain all ids of clients currently connected
    listOfClientsOnlineId = []
    # A list that will contains all the clients that are currently talking to each other
    connectedPair = []

    # potential_readers , potential_writes, potential_errors that will be passed to the select
    # potential_readers is a list of all the sockets that are ready to be read from
    potential_readers = [tcpSocket, udpSocket]
    # potential_writes is a list of all the sockets that are ready to be written to
    potential_writes = []
    # potential_errors is a list that will contain errors from handling socket - currently does nothing might be used later
    potential_errors = []
    # A queue that will hold the message
    ClientMessageQueue = {}
    
    # Bind the TCP socket
    while(tcpNotBound):
        try:
            PORT = secrets.choice(PORTS)
            tcpSocket.bind(('localhost', PORT))
            tcpNotBound = False
        except socket.error as e:
            print(str(e))

    # Bind the UDP socket
    while(udpNotBound):
        try:
            udpSocket.bind(('localhost', PORT))
            udpNotBound = False
        except socket.error as e:
            print(str(e))

    if DEBUG_MODE:
        print(tcpSocket, udpSocket)

    # Insert usrs from DB query into usr dictionary
    for usr in usrTableResult:
        usrDict = {'password': usr.pwd, 'salt':None, 'saltedPassword':None, 'portNumber': PORT, 'cookie':None, 
        'lastSeen': None, 'socket':None, 'kasocket':None}
        clients[int(usr.usr_id)] = usrDict

    if DEBUG_MODE:
        print(clients)

    # The TCP server will listen to up to 8 connection
    # This for the TCP  server socket
    tcpSocket.listen(8)

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
            if DEBUG_MODE:
                print(socketTypesRead)
            #################################
            #  UDP SECTION - CONNECT PHASE  #
            #################################   
            if socketTypesRead is udpSocket:
                resp = ""
                data, addr = udpSocket.recvfrom(2048)
                if DEBUG_MODE:
                    print(data, addr)
                data = data.decode('utf-8').split()
                message = ""
                # Receive HELLO from client and send CHALLENGE to client
                if data[0] == "HELLO":
                    if int(data[1]) in clients:
                        clientID = int(data[1])
                        addrToId[addr] = clientID
                        password = clients[clientID]['password']
                        salt = clients[clientID]['salt'] = bcrypt.gensalt()
                        clients[clientID]['saltedPassword'] = bcrypt.hashpw(str(password).encode(), salt)
                        sv.CHALLENGE(udpSocket, clientID, addr, salt)
                # Receive RESPONSE from client and authenticate, send Success or Failure.
                elif data[0] == "RESPONSE":
                    clientID = addrToId[addr]
                    del addrToId[addr] 
                    saltyPassword = data[1]
                    if DEBUG_MODE:
                        print(clients[clientID]['saltedPassword'])
                        print(saltyPassword)
                    if clients[clientID]['saltedPassword'] == saltyPassword.encode():
                        cookie = clients[clientID]['cookie'] = token_urlsafe(16)
                        password = clients[clientID]['password']
                        salt = clients[clientID]['salt']
                        sv.AUTH_SUCCESS(udpSocket, clientID, addr, cookie, str(password), salt, PORT)       
                    else:
                        sv.AUTH_FAIL(udpSocket, clientID, addr)
            ################################
            #  TCP SECTION - CONNECT PHASE #
            ################################
            elif socketTypesRead is tcpSocket:
                #Preconnect Message Read
                connectionSocket, connectionAddress = tcpSocket.accept()
                if DEBUG_MODE:
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
            ################################
            #   TCP SECTION - CHAT PHASE   #
            ################################
            else: 
                # Read and decrypt tcp input string
                id_encBytes = socketTypesRead.recv(4096)
                if len(id_encBytes) < 3:
                    #if invalid message received ignore it
                    continue
                id = int(id_encBytes[:3])
                encBytes = id_encBytes[3:]
                machine = sv.createMachine(id, clients)
                decryptedMessage = machine.decryptMessage(encBytes)
                message = pickle.loads(decryptedMessage)
                if DEBUG_MODE:
                    print(message)

                # Receive CONNECT from client
                if message['messageType'] == 'CONNECT':
                    if message['cookie'] == clients[id]['cookie']:
                        connected_client_id = int(message['senderID'])
                        message = messageDict(senderID='Server', messageType='CONNECTED')
                        pickMessage = pickle.dumps(message)
                        encMessage = machine.encryptMessage(pickMessage)
                        sv.CONNECTED(socketTypesRead, encMessage)
                        listOfClientsOnlineId.append(int(connected_client_id))
                        clients[connected_client_id]['socket'] = socketTypesRead
                    continue

                
                # Receive CHAT_REQUEST from client
                if message['messageType']  == 'CHAT_REQUEST':
                    if DEBUG_MODE:
                        print("CHAT_REQUEST MsgType")
                    # Check the client id and the online id list
                    # Assume that target is already online
                    # We can add a check if needed here to see if the client is busy (due to being in a pair already) 
                    # Can also check if already connected
                    isClientOnline = int(message['targetID']) in listOfClientsOnlineId
                    if (isClientOnline):
                        targetClientIdPair = [tupleElem for tupleElem in connectedPair 
                            if tupleElem[0] == int(message['targetID'])  or tupleElem[1] == int(message['targetID'])]

                        if not targetClientIdPair:

                            connectedPair.append(tuple((int(message['targetID']), int(message['senderID']))))
                            connectionSenderId = message['senderID']
                            connectionTargetId = message['targetID']
                            # Finder chat request sender socket 
                            indexOfSocketId = listOfClientsOnlineId.index(int(connectionSenderId))
                            responseSocket = potential_readers[indexOfSocketId+2] # +2 to account for the already existing sockets
                            #List existing sess ids
                            listExistingSessionIDs = [r.sess_id for r in session.query(chat_sess.sess_id)]
                            SessionID = sesessionIdGen(listExistingSessionIDs)
                            # CHAT_STARTED RES here 
                            sv.CHAT_STARTED(responseSocket,SessionID,connectionTargetId,machine)
                            indexOfSocketId = listOfClientsOnlineId.index(int(connectionTargetId))
                            responseSocket = potential_readers[indexOfSocketId+2]
                            machine2 = sv.createMachine(connectionTargetId, clients)
                            sv.CHAT_STARTED(responseSocket,SessionID,connectionSenderId,machine2)
                            # Add SessionID and users in the session to DB
                            sessEntry = chat_sess(sess_id = int(SessionID), usr_id1 = int(connectionSenderId), usr_id2 = int(connectionTargetId))
                            session.add(sessEntry)
                            session.commit()
                        else:
                            # Send a message about client is online but a busy
                            connectionSenderId = message['senderID']
                            connectionTargetId = message['targetID']
                            indexOfSocketId = listOfClientsOnlineId.index(int(connectionSenderId))
                            responseSocket = potential_readers[indexOfSocketId+2]
                            machine = sv.createMachine(connectionSenderId, clients)
                            sv.UNREACHABLE(responseSocket,connectionTargetId, machine)

                            
                    else:
                        #send a message about the client being offline
                        connectionSenderId = message['senderID']
                        connectionTargetId = message['targetID']
                        indexOfSocketId = listOfClientsOnlineId.index(int(connectionSenderId))
                        responseSocket = potential_readers[indexOfSocketId+2]
                        machine = sv.createMachine(connectionSenderId, clients)
                        sv.UNREACHABLE(responseSocket,connectionTargetId, machine)
                    # continue to avoid sending back
                    continue

                # Receive chat END_REQUEST from client.
                if message['messageType'] == 'END_REQUEST':
                    if DEBUG_MODE:
                        print(message)
                    # Send disonnect notification message to clients
                    sv.disconnectMsg(message, clients, potential_readers, listOfClientsOnlineId)
                    #TODO move the line above to line 262
                    # Find the target pair from the  connectedPair list
                    targetClientIdPair = [tupleElem for tupleElem in connectedPair if tupleElem[0] == int(message['senderID']) or tupleElem[1] == int(message['senderID'])]
                    if DEBUG_MODE:
                        print("targ")
                        print(targetClientIdPair)
                        print("con")
                        print(connectedPair)
                    # Remove from the list
                    if targetClientIdPair:
                        connectedPair.remove(targetClientIdPair[0])                    
                    continue

                #Receive KEEP_ALIVE requests
                if message['messageType'] == 'KEEP_ALIVE':
                    kaID = int(message['senderID'])
                    if clients[kaID]['kasocket'] is None:
                        clients[kaID]['kasocket'] = socketTypesRead
                    print('Received keep alive from:', kaID)
                    clients[kaID]['lastSeen'] = datetime.now()


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
                    # Add message to DB
                    msgEntry = msgs(sess_id=int(message['sessionID']), time=datetime.now(), sender_id=int(message['senderID']), msg_body=message['messageBody'] )
                    session.add(msgEntry)
                    session.commit()

                    # If the socket is not in potential_writes to send form later
                    if socketTypesRead not in potential_writes:
                        potential_writes.append(socketTypesRead)
                # none msgObject ?
                else:
                    # TODO: Check if needed, or change implementation.
                    # Remove the socket from the potential_writes to avoid
                    if socketTypesRead in potential_writes:
                        potential_writes.remove(socketTypesRead)
                    potential_readers.remove(socketTypesRead)
                    # Close the socket
                    socketTypesRead.close()
                    # Delete the client socket message
                    del ClientMessageQueue[socketTypesRead]

        '''
        # Checking last seen status of clients
        idsToRemove = []
        print(listOfClientsOnlineId)
        for clientID in listOfClientsOnlineId:
            lastSeen = clients[clientID]['lastSeen']
            #TODO remove the line below once keep alive is working. 
            lastSeen = lastSeen if lastSeen is not None else datetime.now()
            print(lastSeen)
            currentTime = datetime.now()
            print(currentTime)
            diff =  currentTime - lastSeen 
            print(diff.seconds)
            if diff.seconds > 180:
                if True:
                    print('Logging off client:', clientID)
                idsToRemove.append(clientID)
                #remove socket
                socketToRemove = clients[connected_client_id]['socket']
                if socketToRemove in potential_readers:
                    potential_readers.remove(socketToRemove)
                if socketToRemove in potential_writes:
                    potential_writes.remove(socketToRemove)
                #disconnect the other client in chat with them if there is one.
                targetClientIdPair = [tupleElem for tupleElem in connectedPair if tupleElem[0] == clientID or tupleElem[1] == clientID]
                if targetClientIdPair:
                    connectedPair.remove(targetClientIdPair[0])
                    if targetClientIdPair[0][0] == clientID:
                        sendNotifToID = targetClientIdPair[0][1]
                    else:
                        sendNotifToID = targetClientIdPair[0][0]
                    machine = sv.createMachine(sendNotifToID, clients)
                    sv.END_NOTIF(clients[sendNotifToID]['socket'], 0, machine)

        for id in idsToRemove:
            listOfClientsOnlineId.remove(id)
        '''

        #####################################################
        #   TCP SECTION - CHAT PHASE - MESSAGE FORWARDING   #
        #####################################################
        for socketTypesWrite in select_ready_to_write:
            try:
                # get the message from the client messages queue
                msgOn = ClientMessageQueue[socketTypesWrite].get_nowait()
                potential_writes.remove(socketTypesWrite)
            except queue.Empty:
                # Remove the writable socket
                potential_writes.remove(socketTypesWrite)
            try:
                if DEBUG_MODE:
                    print(listOfClientsOnlineId)
                    print('=================')

                # Send the message to the target client socket

                # This based on using the target client id to find the target client socket in the list and then send
                # the message to it. Currently it depends on using client message object that contain the target id
                # like the TCP message idea of having source and target address
                idTarget = [tupleElem for tupleElem in connectedPair if tupleElem[0]== int(msgOn['senderID']) or tupleElem[1] == int(msgOn['senderID'])]
                if idTarget[0][1] == int(msgOn['senderID'])  :
                    targetClient = listOfClientsOnlineId.index(int(idTarget[0][0]))
                else:
                    targetClient = listOfClientsOnlineId.index(int(idTarget[0][1]))
                msgTargetIndex = 2 + targetClient # + 2 to account for the UDP and TCP socket in the list 
                targetID = int(msgOn['targetID'])
                machine3 = sv.createMachine(targetID, clients)
                pickMessage = pickle.dumps(msgOn)
                encMessage = machine3.encryptMessage(pickMessage)
                totMessage = encMessage
                potential_readers[msgTargetIndex].send(totMessage) 
                if DEBUG_MODE:
                    print(connectedPair)
                    print("potential_readers sent")
            except Exception as e:
                if DEBUG_MODE:
                    print("Exception: ", str(e), " was raised ")