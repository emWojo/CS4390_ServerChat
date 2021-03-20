import base64
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class aesCipher:

    def __init__(self, key):
        self.blockSize = AES.block_size
        self.key = key

    def encryptMessage(self, input):
        if type(input) != bytes:
            input = input.encode()
        input = pad(input, self.blockSize)
        #create a random initialization vector
        iv = Random.new().read(self.blockSize)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        encBytes = cipher.encrypt(input)
        ivPlusMessage = iv + encBytes
        return base64.urlsafe_b64encode(ivPlusMessage)

    def decryptMessage(self, b64String):
        ivPlusMessage = base64.urlsafe_b64decode(b64String)
        iv = ivPlusMessage[:self.blockSize]
        encBytes = ivPlusMessage[self.blockSize:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        paddedOutput = cipher.decrypt(encBytes)
        return unpad(paddedOutput, self.blockSize)
