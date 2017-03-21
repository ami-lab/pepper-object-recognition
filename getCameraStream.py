# -*- encoding: UTF-8 -*-
# Get an image from NAO. Display it and save it using PIL.
import sys
import numpy
import cv2
from pepperImageProvider import PepperImageProvider

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
	imageProvider = PepperImageProvider(IP, PORT, FPS)
	imageProvider.connect()
	while(True):
		img = imageProvider.getCvImage()
		cv2.imshow("Image", img)
		k = cv2.waitKey(1)
		if k==27:    # Esc key to stop
			cv2.destroyAllWindows()
			break

	imageProvider.disconnect()