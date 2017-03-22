# -*- encoding: UTF-8 -*-
# Get an image from NAO. Display it and save it using PIL.
import sys
import numpy
import cv2
import time
from pepperImageProvider import PepperImageProvider
import threading

def printFps(imageProvider):
	if imageProvider.connected:
		threading.Timer(1, printFps, args=[imageProvider]).start()	
		print "FPS:" + str(imageProvider.getImagesCounter())
		imageProvider.reset()



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

	

	# do something else, such as
	imageProvider = PepperImageProvider(IP, PORT, FPS)
	imageProvider.connect()
	printFps(imageProvider)

	while(True):
		img = imageProvider.getCvImage()
		cv2.imshow("Image", img)
		k = cv2.waitKey(1)
		if k==27:    # Esc key to stop
			cv2.destroyAllWindows()
			break
	imageProvider.disconnect()
 
