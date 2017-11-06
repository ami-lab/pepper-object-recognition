import base64
import requests
import urllib2
import os
import cv2
import json
from inspect import getmodule
from multiprocessing import Pool


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

class FaceRecognizerAPI:
    def enrollByFolder(self, folderPath):
        for file in os.listdir(folderPath):
            imagePath = os.path.join(folderPath, file)
            if(imagePath.endswith(".png")):
                f = open(imagePath, 'r')
                img = f.read()
                self.enroll(img, "Stefania")

    def enroll(self, cv_image, name):
        url = 'https://api.kairos.com/enroll'
        image64 = base64.b64encode(cv_image)
        values = {
            "image": image64,
            "subject_id": name,
            "gallery_name": "MyGallery"
        }
        print(self.send_request(url,json.dumps(values)))

    @async
    def recognize(self, cv_image):
        url = 'https://api.kairos.com/recognize'
        image64 = base64.b64encode(cv_image)
        values = {
            "image": image64,
            "gallery_name": "MyGallery"
        }
        jsonResponse = json.loads(self.send_request(url, json.dumps(values)))
        #print(json.dumps(jsonResponse, sort_keys=True,indent=4, separators=(',', ': ')))
        if 'images' in jsonResponse and len(jsonResponse['images'] )> 0 and 'transaction' in jsonResponse['images'][0]:
            transactionJson = jsonResponse['images'][0]['transaction']
            if 'subject_id' in transactionJson:
                if (transactionJson != -1):
                    recognizedPerson = transactionJson['subject_id']
                    print(recognizedPerson)
                return transactionJson
            else:
                return -1
        else:
            return -1

    def send_request(self, url, values):
        Appname = "alexandru.gavril.florin+kairos@gmail.com's App"
        AppID = "b873911a"
        Key = "c387bfe094a172a08cbde7babc7caa34"

        headers = {
          'Content-Type': 'application/json',
          'app_id': AppID,
          'app_key': Key
        }
        request = urllib2.Request(url, data=values, headers=headers)
        response_body = urllib2.urlopen(request).read()
        return response_body


class FaceRecognizerCV:
    def __init__(self, folder):
        images, labels = self.getTrainData(folder)
        self.recognizer = cv2.face.createLBPHFaceRecognizer()
        self.train(images, labels)
        self.names = { 0: "Alex", 1:"Stephanie"}

    def getTrainData(self, folderPath):
        all_classes = [dir for dir in os.listdir(folderPath)]
        images = []
        labels = []
        for dir in all_classes:
            cDirImages = self.getImagesInFolder(os.path.join(folderPath, dir))
            images.extend(cDirImages)
            labels.extend([int(dir) for image in cDirImages])

        return images, labels


    def getImagesInFolder(self, folderPath):
        images = [cv2.cvtColor(cv2.imread(os.path.join(folderPath, file)),cv2.COLOR_BGR2GRAY) for file in os.listdir(folderPath) if file.endswith(".png")]
        return images

    def train(self, images, labels):
        import numpy as np
        self.recognizer.train(images, np.array(labels))

    def getNameForClass(self, label):
        return self.names[int(label)]

    def recognize(self, image):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        result = cv2.face.MinDistancePredictCollector()
        self.recognizer.predict(image, result, 0)
        nbr_predicted = result.getLabel()
        conf = result.getDist()

        print(str(nbr_predicted) + " " + str(conf))
        return self.getNameForClass(nbr_predicted)


