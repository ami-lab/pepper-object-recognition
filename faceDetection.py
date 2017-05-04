import time

# Python Image Library
import Image

from naoqi import ALProxy
import numpy
import cv2
from copy import deepcopy

class FaceDetector:
	def __init__(self, cascadePath="haarcascade_frontalface_default.xml"):
		self.face_cascade = cv2.CascadeClassifier(cascadePath)

	def detect(self, image):
		gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
		return faces


	def drawFaces(self, image, faces):
		img = deepcopy(image)
		for (x, y, w, h) in faces:
			cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
		return img