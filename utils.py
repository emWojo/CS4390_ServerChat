import os

#Global Constants
TIMEOUT_VAL = 3000

def messageDict(senderID, messageType, messageBody=None, 
targetID=None, sessionID=None, cookie=None 
,port=None,  hashedPassword=None, salt=None):
    return { 
    'senderID' : senderID, 
    'messageType' : messageType,
    'messageBody' : messageBody,
    'targetID' : targetID,
    'sessionID': sessionID,
    'cookie': cookie,
    'port' :port,
    'hashedPassword': hashedPassword,
    'salt':salt
    }

from uuid import uuid4

def sesessionIdGen(listOfExistingSessionIDs):
    while True:
        i = uuid4().int
        mask = '0b111111111111111111111111111111111111111111111111111111111111111'
        i = i & int(mask, 2)
        if i not in listOfExistingSessionIDs:
            return i#
            

def screenClear():
    if os.name == 'posix':
        os.system('clear')
    else:
        os.system('cls')
