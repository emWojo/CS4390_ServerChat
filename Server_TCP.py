import socket
import select
import threading
import pickle
import queue
from MessageObject import MessageObject

print("Server Runing")

serverSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
udpSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
#serverSocket.set_reuse_addr()
serverSocket.setblocking(False)

try:
    serverSocket.bind(('localhost', 6265))
except socket.error as e:
    print(str(e))
try:
    udpSocket.bind(('localhost', 6265))
except socket.error as e:
    print(str(e))
print(serverSocket)
# Make this a  server

# UDP
clients = {111:100, 222:200, 333:300} #temp
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
                resp = "CHALLENGE "+str(123)
                print("challenge")
            else:
                del addrToId[addr]
                print("fail challenge")
        elif data[0] == "RESPONSE":
            if clients[addrToId[addr]] == int(data[1]):
                resp = "AUTH_SUCCESS"
                print("succ")
            else:
                del addrToId[addr]
                resp = "AUTH_FAIL"
                print("fail")
        udpSocket.sendto(str.encode(resp),addr)
    udpSocket.close()
threading.Thread(target=udp_thread).start()

# TCP
serverSocket.listen(4)

listOfClientSocketOnline = []
listOfClientsOnlineId = []
connectedPair = []
potential_readers = [serverSocket]
potential_writes = []
potential_errors = []
ClientMessageQueue = {}
while True:
        #print("Loop Server")
        #  Select 
        select_ready_to_read , select_ready_to_write, select_error = select.select(potential_readers,potential_writes,potential_errors)
        for socketTypesRead in select_ready_to_read:
            if socketTypesRead is serverSocket:
                # Accepts Clients Chat Phase
                connectionSocket,connectionAddress = serverSocket.accept()
                print(connectionSocket)
                print(connectionAddress)
                # Prevent connection from blocking
                connectionSocket.setblocking(False)
                # Connection Will each have a queue
                potential_readers.append(connectionSocket)

                # Save the client id to list
                #listOfClientsOnlineId.append(clientId)
                listOfClientSocketOnline.append(connectionSocket)
                ClientMessageQueue[connectionSocket] = queue.Queue()
            else:
                msgObject = socketTypesRead.recv(4096)
                msgObjectDecoded = pickle.loads(msgObject)

                print(msgObjectDecoded)
                #decodeMsg = msgObject.decode('utf-8')
                # Add to connected client list
                if msgObjectDecoded.msgType == 'HELLO' :
                   print("HELLO MsgType")
                   #print(msgObjectDecoded.msgBody)
                   #print(msgObjectDecoded.senderId)
                   #socketTypesRead.send(bytes("Connected to server and added client Id",'utf-8'))
                   listOfClientsOnlineId.append(msgObjectDecoded.senderId)
                   print(listOfClientsOnlineId)
                   continue
                if msgObjectDecoded.msgType == 'CHATSET' :
                   print("CHATSET MsgType")
                   print("Connect to")
                   print(msgObjectDecoded.targetId)
                   print(listOfClientsOnlineId)
                   # Assume that target is already online
                   # We can add a check if needed
                   # Can Check also if already connected
                   connectedPair.append(tuple((int(msgObjectDecoded.targetId), msgObjectDecoded.senderId)))
                   continue
                if msgObjectDecoded.msgBody == 'end talk':
                    print(msgObject)
                    #close the socket of the ccurrent connection
                    #close the other client socket
                    #break
                    # end client threads
                    socketTypesRead.send(bytes("end talk",'utf-8'))

                if msgObjectDecoded.msgBody == 'end server':
                    print(msgObject)
                    print(listOfClientSocketOnline)
                    #close all socket of the ccurrent connection
                    for conections in listOfClientSocketOnline:
                         # Inform the clients of the closure
                         conections.close()
                    # end all clients threads
                    # ClientMessageQueue[connectionSocket]close ?
                    serverSocket.close()
                    exit(0)
                    #break
                # Valid
                print("msgObject")
                #print(str(msgObject) )

                # behave like a message
                if msgObject: # might be none
                    ClientMessageQueue[socketTypesRead].put(msgObject)
                    # Valid
                    if socketTypesRead not in potential_writes:
                        potential_writes.append(socketTypesRead)
                # none msgObject
                else:
                    if socketTypesRead  in potential_writes:
                        potential_writes.remove(socketTypesRead)

                    potential_readers.remove(socketTypesRead)
                    socketTypesRead.close()
                    del ClientMessageQueue[socketTypesRead]
        for socketTypesWrite in select_ready_to_write:
            try:
                msgOn = ClientMessageQueue[socketTypesWrite].get_nowait()
            except queue.Empty:
                potential_writes.remove(socketTypesWrite)

            else:
                print(listOfClientsOnlineId)
                print(int(msgObjectDecoded.targetId))
                print(connectedPair)
                try:
                    print(int(msgObjectDecoded.targetId))
                    print(int(msgObjectDecoded.senderId))
                    print(listOfClientsOnlineId)
                    print('=================')
                    print(listOfClientsOnlineId.index(int(msgObjectDecoded.targetId)))
                    #potential_readers[int(msgObjectDecoded.targetId)].send(msgOn)
                    potential_readers[1+(listOfClientsOnlineId.index(int(msgObjectDecoded.targetId)))].send(msgOn)

                    print("poti_reader")
                    #print(listOfClientsOnlineId.index(int(msgObjectDecoded.senderId)))
                        #potential_readers[1]

                except Exception as e:
                    print("error")
                    print(e)




