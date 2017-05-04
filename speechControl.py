from naoqi import ALProxy

class SpeechController:
    def __init__(self, ip, port):
        self.IP = ip
        self.PORT = port
        self.speech = ALProxy("ALTextToSpeech", self.IP, self.PORT)

    def say(self, text):
        self.speech.say(text)
