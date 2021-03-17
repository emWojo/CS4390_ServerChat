class MessageObject:

    def __init__(self, msgType, senderId, msgBody=None, targetId=None):
        self.msgType = msgType
        self.senderId = senderId
        if  msgBody is None:
            self.msgBody = []
        else:
            self.msgBody= msgBody
        if targetId is None:
            self.targetId = []
        else:
            self.targetId = targetId
