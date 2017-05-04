# -*- encoding: UTF-8 -*-
# Get an image from NAO. Display it and save it using PIL.
import sys
import numpy as np
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
	calibration = False
	CALIBRATION_IMAGES_NO = 0

	# Read IP address from first argument if any.
	if len(sys.argv) > 2:
		IP = sys.argv[1]
		if sys.argv[2].isdigit():
			FPS = int(sys.argv[2])
		else:
			print("FPS is not numerical!")
		if len(sys.argv) > 3:
			if sys.argv[3].isdigit():
				calibration = True
				CALIBRATION_IMAGES_NO = int(sys.argv[3])
			else:
				print("Calibration Images No is not numerical! Not running calibration.")
		
		print(FPS)
	elif(len(sys.argv) > 1):
		IP = sys.argv[1]
	else:
		print("Usage: getCameraStream <Pepper_IP> OPT:<FPS> <CALIBRATION_IMAGES_NO>")
		exit(-1)

	

	# do something else, such as
	imageProvider = PepperImageProvider(IP, PORT, FPS)
	imageProvider.connect()
	printFps(imageProvider)
	# termination criteria
	criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

	# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
	cbrow = 9
	cbcol = 7
	objp = np.zeros((cbrow * cbcol, 3), np.float32)
	objp[:, :2] = np.mgrid[0:cbcol, 0:cbrow].T.reshape(-1, 2)


	# Arrays to store object points and image points from all the images.

	objpoints = [] # 3d point in real world space
	imgpoints = [] # 2d points in image plane.
	calibCnt = 0
	while(True):
		img = imageProvider.getCvImage()
		cv2.imshow("Image", img)

		if calibration:
			gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
			# Find the chess board corners
			ret, corners = cv2.findChessboardCorners(gray, (cbcol, cbrow), None)
			if ret == True:
				objpoints.append(objp)
				corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
				imgpoints.append(corners2)
				# Draw and display the corners
				img = cv2.drawChessboardCorners(gray, (7,9), corners2,ret)
				cv2.imshow('Corners',gray)
				calibCnt = calibCnt + 1
				if calibCnt >= CALIBRATION_IMAGES_NO:
					print("Running Calibration...")
					ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1],None,None)
					print(ret)
					print(mtx)
					print(dist)
					print(rvecs)
					print(tvecs)
					break
		 

		k = cv2.waitKey(1)
		if k==27:    # Esc key to stop
			cv2.destroyAllWindows()
			break
 


	if calibration:
		img = imageProvider.getCvImage()
		cv2.imshow("Image", img)
		imageProvider.disconnect()
		h,  w = img.shape[:2]
		newcameramtx, roi=cv2.getOptimalNewCameraMatrix(mtx,dist,(w,h),1,(w,h))

		dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
		cv2.imwrite('beforeCalibresult.png', img)
		cv2.imwrite('calibresult.png',dst)
		#f = open('cameraCalib.txt', 'w')
		line1 = str(mtx[0,0]) + " " + str(mtx[1,1]) + " " + str(mtx[0,2]) + " " + str(mtx[1,2])
		line2 = str(dist[0,0]) + " " + str(dist[0,1]) + " " + str(dist[0,2]) + " " + str(dist[0,3])
		print(line1 + " " + line2)

		line3 = "full"
		line4 = "640 480"
		print(line3)
		print(line4)
		
		#f.close()

	
		
 
