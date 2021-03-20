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