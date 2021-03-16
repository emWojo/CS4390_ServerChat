import os
import pickle
import socket
import sys
import threading
from appJar import gui
from MessageObject import MessageObject  # from ProtocolMessage can be use if multie class select ?

var = MessageObject("", -1, -1, -1)
appWindow = gui()


# This method will execute once the send button in the GUI is clicked
def pressSendButton():
    var.msgBody = appWindow.getEntry('EntrySend')
    # The client id, most likely a temporary placement
    var.senderId = 222
    if var.msgBody.split()[0] == "chat":

        var.MsgType = "CHAT_REQUEST"
        var.targetId = var.msgBody.split()[1]

    else:
        var.MsgType = "MESSAGE"
    dataStr = pickle.dumps(var)
    socketServOne.send(dataStr)


# This method will build the GUI
def guiBuilder():
    appWindow.setSize("400x400")
    appWindow.addLabel("Cl-2", "Client-2")
    appWindow.addScrolledTextArea("TextAreaScroll", text=None)
    appWindow.addEntry("EntrySend")
    appWindow.addButton("Send", pressSendButton)


# This method will run on it own thread
# to allow the client to send and receive data without blocking
def msgRecv():
    keepChat = False
    while keepChat == False:
        data = (socketServOne.recv(1024))
        # Handle object data
        try:
            # Unpickle data
            dataMsg = pickle.loads(data)
            appWindow.setTextArea('TextAreaScroll', str(dataMsg.msgBody) + '\n')

        # Handle normal data type  data
        except:
            appWindow.setTextArea('TextAreaScroll', str(data.decode()) + '\n')


def msgSend():
    var.msgBody = appWindow.getEntry('EntrySend')
    dataStr = pickle.dumps(var)
    socketServOne.send(dataStr)


socketServOne = socket.socket()
socketServOne.connect(('localhost', 6565))

# Send an object to the server to connect Inculde the message HELLO and sender id so
# the client can be added to connected clients list
var.MsgType = "HELLO"
var.senderId = 222
# Pickle data so it can be serialized
dataStr = pickle.dumps(var)
# Send data to the server
socketServOne.send(dataStr)

# Start the client message receiver thread
threading.Thread(target=msgRecv).start()

# start the GUI
guiBuilder()
appWindow.go()
# Exit and end thread
# Exit and end thread
socketServOne.close()
os._exit(0)
