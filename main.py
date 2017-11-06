from pepperImageProvider import PepperImageProvider
from faceDetection import FaceDetector
from faceRecognition import FaceRecognizerAPI
from faceRecognition import FaceRecognizerCV
from postureControl import PostureController
from speechControl import SpeechController
from naoqi import ALProxy
from inspect import getmodule
from multiprocessing import Pool
import qi

from copy import deepcopy
import cv2
import time
import json

ip = "192.168.0.115"
port = 9559
frameRate = 20
degrees = 20
facesFolder = "faces"

imageProvider = PepperImageProvider(ip, port, frameRate)
postureController = PostureController(ip, port)
faceDetector = FaceDetector()
faceRecognizer = FaceRecognizerCV(facesFolder)
speechController = SpeechController(ip, port)

postureController.applyHomePosture()
imageProvider.connect()
croppedFaces = []

knownPeople = ["Alex", "Stephanie"]

def async(decorated):
    r'''Wraps a top-level function around an asynchronous dispatcher.

        when the decorated function is called, a task is submitted to a
        process pool, and a future object is returned, providing access to an
        eventual return value.

        The future object has a blocking get() method to access the task
        result: it will return immediately if the job is already done, or block
        until it completes.

        This decorator won't work on methods, due to limitations in Python's
        pickling machinery (in principle methods could be made pickleable, but
        good luck on that).
    '''
    # Keeps the original function visible from the module global namespace,
    # under a name consistent to its __name__ attribute. This is necessary for
    # the multiprocessing pickling machinery to work properly.
    module = getmodule(decorated)
    decorated.__name__ += '_original'
    setattr(module, decorated.__name__, decorated)

    def send(*args, **opts):
        pool = Pool(processes=1)
        return pool.apply_async(decorated, args, opts)

    return send

topic_ids = []
should_move = True

said = False



class Main:

    def __init__(self):
        try:
            connection_url = "tcp://" + ip + ":" + str(port)
            app = qi.Application(["UserIdentifier", "--qi-url=" + connection_url])
        except RuntimeError:
            print("Can't connect to Naoqi at ip \"" + ip + "\" on port " + str(port) + ".\n"
             "Please check your script arguments. Run with -h option for help.")
            exit(-1)
        self.app = app
        self.app.start()
        self.session = app.session


        self.subscribers_list = []
        self.memory = self.session.service("ALMemory")
        self.people_detection = self.session.service("ALPeoplePerception")

        self.people_detection.subscribe("PeopleDetection")
        self.connect_callback("PeoplePerception/PeopleDetected", self.on_people_detected)
        self.connect_callback("PeoplePerception/PopulationUpdated", self.on_people_updated)
        self.counter = 0
        self.speech_recognition = self.session.service("ALSpeechRecognition")
        self.speech_recognition.subscribe("SpeechRecognition")

        self.peoplePositions = {}
        self.speech_recognition_topics = (
            'topic: ~main_topic()\n'
            'language: enu\n'
            'u:(Yes) $person=Alex\n'
            'u:(No) $person=Stephanie\n'
        )

        # Handler for greeting.
        self.greeting_handler = self.memory.subscriber("person")
        self.greeting_handler.signal.connect(self.on_person_heard_detected)
        self.searchedPerson = None
        self.is_speech_recognition_started = False
        self.start_speech_recognition()

        # Connects to the service for dialog.
        self.dialog = self.session.service("ALDialog")
        self.dialog.setLanguage("English")

        for topic in [self.speech_recognition_topics]:
            topic_id = self.dialog.loadTopicContent(topic)
            topic_ids.append(topic_id)
            self.dialog.activateTopic(topic_id)

        self.dialog.subscribe('main_topic')

    def start_speech_recognition(self):
        if not self.is_speech_recognition_started:
            try:
                self.speech_recognition.setVocabulary(["Yes", "No"], False)
            except RuntimeError:
                print("ASR already started")

            self.speech_recognition.subscribe("main_topic")
            self.is_speech_recognition_started = True
            print("Speech recognition started.")

    def stop_speech_recognition(self):
        if self.is_speech_recognition_started:
            self.speech_recognition.unsubscribe("main_topic")
            self.is_speech_recognition_started = False
            print("Speech recognition stopped.")

        self.dialog.unsubscribe('main_topic')
        for topic_id in topic_ids:
            self.dialog.deactivateTopic(topic_id)
            self.dialog.unloadTopic(topic_id)

            self.stalker = False

    def on_person_heard_detected(self, person):
        speechController.say("Heard person " + person)
        self.findPerson(person)

    def connect_callback(self, event_name, callback_func):
        subscriber = self.memory.subscriber(event_name)
        subscriber.signal.connect(callback_func)
        self.subscribers_list.append(subscriber)

    def get_person_info(self, person):
        print("\t Person ID: " + str(person[0]))
        person_info = {"id": person[0],
                       "dist": person[1],
                       "coordinate": self.memory.getData("PeoplePerception/Person/" + str(person[0]) + "/PositionInWorldFrame"),
                       "coordRobotFrame": self.memory.getData("PeoplePerception/Person/" + str(person[0]) + "/PositionInRobotFrame")
                      }
        return person_info

    def on_people_updated(self, people):
        if people == None or people == [] or len(people) == 0:
            should_move = True
            return

    def on_people_detected(self, people):
        if self.searchedPerson == None:
            print("No person to search!?")
            return

        self.counter = self.counter + 1
        print("Detected People...." + str(self.counter))
        should_move = False
        if people == [] or len(people) == 0 or len(people[1]) == 0:
            should_move = True
            return



        faces = faceDetector.detect(self.image)
        print("Found " + str(len(faces)) + " faces")

        if len(faces) == 0:
            #if(not said):
                #speechController.say("Please move towards me. I cannot see your face.")
            said = True
        else:
            print("Looking for..." + self.searchedPerson)
            if(self.searchedPerson != None):
                for face in faces:
                    (x, y, w, h) = face
                    croppedImage = self.image[y: y + h, x: x + w]
                    name = faceRecognizer.recognize(croppedImage)
                    print("Recognized: " + name)

                    if(name == self.searchedPerson):
                        if(len(people[1]) >= 1):
                            postureController.stopExplore()
                            person_info = self.get_person_info(people[1][0])
                            self.searchedPerson = None
                            print("Going to " + str(person_info['coordRobotFrame']))
                            postureController.navigateTo(person_info['coordRobotFrame'][0], person_info['coordRobotFrame'][1])
                            self.say("Reached Stephanie")
                        else:
                            print("Too many faces or people I don't really know, here!")
                    else:
                        should_move = True

    def updateImage(self):
        self.image = imageProvider.getCvImage()
        cv2.imshow("Image", self.image)
        cv2.waitKey(1)

    def say(self, text):
        pool = Pool(processes=1)  # Start a worker processes.
        result = pool.apply_async(speechController.say(text), [], None)

    def matchFace(self, face, person_info):
        (x, y, w, h) = face
        croppedImage = self.image[y: y + h, x: x + w]
        name = faceRecognizer.recognize(croppedImage)

        if name not in self.peoplePositions:
            speechController.say("Hi, " + name)
            self.peoplePositions[name] = person_info
            knownPeople.remove(name)
            postureController.motion.moveTo(person_info['coordRobotFrame'][0],person_info['coordRobotFrame'][1], 0.0)
            postureController.stopExplore()
        print(name + " " + str(person_info['coordinate']))

    def findPerson(self, name):
        try:
            self.searchedPerson = name
            should_move = True
            pool = Pool(processes=1)  # Start a worker processes.
            result = pool.apply_async(postureController.explore(),[] , None)


        except KeyboardInterrupt:
            print("Script interrupted by user, shutting down.")
            imageProvider.disconnect()
            self.stop_speech_recognition()
            postureController.stopExplore()

    """
    def findPerson(self, name):
        try:
            self.searchedPerson = name
            should_move = True
            while (self.searchedPerson != None):
                if (should_move):
                    postureController.rotate(degrees)
                    said = False
        except KeyboardInterrupt:
            print("Script interrupted by user, shutting down.")
            imageProvider.disconnect()
            self.stop_speech_recognition()
    """

    def run(self):
        print ("Running...")
        try:
            while True:
                self.updateImage()

        except KeyboardInterrupt:
            print("Script interrupted by user, shutting down.")
            imageProvider.disconnect()
            self.stop_speech_recognition()
            postureController.stopExplore()




m = Main()
m.run()