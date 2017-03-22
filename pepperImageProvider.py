import time

# Python Image Library
import Image

from naoqi import ALProxy
import numpy
import cv2

class PepperImageProvider:

	def __init__(self, IP, PORT, FPS):
		self.IP = IP
		self.PORT = PORT
		self.FPS = FPS
		self.connected = False
		self.imagesCounter = 0

	def getImagesCounter(self):
		return self.imagesCounter

	def reset(self):
		self.imagesCounter = 0

	def connect(self):
		self.camProxy = ALProxy("ALVideoDevice", self.IP, self.PORT)
		resolution = 2    # VGA
		colorSpace = 11   # RGB
		self.videoClient = self.camProxy.subscribe("python_client", resolution, colorSpace, self.FPS)
		self.connected = True

	def getCvImage(self):
		if(not self.connected):
			raise Exception('Al Proxy not initialized.!') 
		# Get a camera image.
		# image[6] contains the image data passed as an array of ASCII chars.
		naoImage = self.camProxy.getImageRemote(self.videoClient)

		self.imagesCounter = self.imagesCounter + 1
		# Get the image size and pixel array.
		imageWidth = naoImage[0]
		imageHeight = naoImage[1]
		array = naoImage[6]

		# Create a PIL Image from our pixel array.
		im = Image.fromstring("RGB", (imageWidth, imageHeight), array)
		opencvImage = cv2.cvtColor(numpy.array(im), cv2.COLOR_RGB2BGR)
		return opencvImage

	def disconnect(self):
		self.camProxy.unsubscribe(self.videoClient)
		self.connected = False