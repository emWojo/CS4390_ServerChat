class MessageObject:

    def __init__(self, MsgType, senderId, msgBody=None, targetId=None):
        self.MsgType = MsgType
        self.senderId = senderId
        if  msgBody is None:
            self.msgBody = []
        else:
            self.msgBody= msgBody
        if targetId is None:
            self.targetId = []
        else:
            self.targetId = targetId
