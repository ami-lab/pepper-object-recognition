# -*- encoding: UTF-8 -*-
# Get an image from NAO. Display it and save it using PIL.

import sys
import time

# Python Image Library
import Image

from naoqi import ALProxy
import numpy
import cv2


def connect_video_device(IP, PORT, FPS):
	camProxy = ALProxy("ALVideoDevice", IP, PORT)
	resolution = 2    # VGA
	colorSpace = 11   # RGB
	videoClient = camProxy.subscribe("python_client", resolution, colorSpace, FPS)

def getImage(camProxy):
  
	# Get a camera image.
	# image[6] contains the image data passed as an array of ASCII chars.
	t0 = time.time()
	naoImage = camProxy.getImageRemote(videoClient)

	t1 = time.time()

	# Time the image transfer.
	print "acquisition delay ", t1 - t0



	# Now we work with the image returned and save it as a PNG  using ImageDraw
	# package.

	# Get the image size and pixel array.
	imageWidth = naoImage[0]
	imageHeight = naoImage[1]
	array = naoImage[6]

	# Create a PIL Image from our pixel array.
	im = Image.fromstring("RGB", (imageWidth, imageHeight), array)
	opencvImage = cv2.cvtColor(numpy.array(im), cv2.COLOR_RGB2BGR)
	return opencvImage
 

if __name__ == '__main__':
	IP = "nao.local"  # Replace here with your NaoQi's IP address.
	PORT = 9559
	FPS = 20

	# Read IP address from first argument if any.
	if len(sys.argv) > 1:
		IP = sys.argv[1]
	if(len(sys.argv) == 3):
		if sys.argv[2].isdigit():
			FPS = int(sys.argv[2])
		else:
			print("FPS is not numerical!")

		print(FPS)
	else:
		print("Usage: getCameraStream <Pepper_IP> OPT:<FPS>")
		exit(-1)

		"""
	First get an image from Nao, then show it on the screen with PIL.
	"""

	camProxy = connect_video_device(IP, PORT, FPS)
	while(True):
		img = getImage(camProxy)
		cv2.imshow("Image", img)
		k = cv2.waitKey(1)
	if k==27:    # Esc key to stop
		cv2.destroyAllWindows()
		break

	camProxy.unsubscribe(videoClient)