#!/usr/bin/python
import sys
import time
from dotstar import Adafruit_DotStar

"""
NOTE: India's chosen color is RED

Usage: <numPositionsToLight> <pos0> ... <posN> 





"""
usageError = "Error --> Usage: python " + sys.argv[0] + " <numPositionsToLight><pos0><...><posN>"

if (len(sys.argv) != 2): 
	print(usageError)
	quit()

argv = list(sys.argv[1])
argv.insert(0, len(argv))
print(argv)

try:
	numPositionsToLight = int(argv[0])
	positionsToLight = []
	for i in range(numPositionsToLight):
	#for i in range(len(argv) - 1):
		newChar = argv[1 + i]
		if (not newChar.isdigit()):
			print 'not a digit!'
			if (newChar == 'a') : positionsToLight.extend((1,2,3))
			elif(newChar == 'b') : positionsToLight.extend((4,5,6))
			elif(newChar == 'c') : positionsToLight.extend((7,8,9))
			continue
		newPos = int(newChar)
		if (newPos == 0):
			continue
		elif (newPos < 1 or newPos > 9):
			raise Exception('Position ' + argv[1 + i] + ' is invalid. Please use numbers between 1 and 9, mapped to the shelves like a number pad')
		elif (newPos == 4):
			newPos = 6
		elif (newPos == 6):
			newPos = 4		
		positionsToLight.append(newPos)
except IndexError:
	print(usageError)
	quit()
except Exception as e:
	#print(type(e))
	print("Error --> " + e.args[0])
	#quit()

# Here's how to control the strip from any two GPIO pins:
datapin   = 10
clockpin  = 11
numpixels = 90
strip     = Adafruit_DotStar(numpixels, datapin, clockpin)

strip.begin()           # Initialize pins for output
strip.setBrightness(64) # Limit brightness to ~1/4 duty cycle

off = 0x000000
red = 0x00FF00
blue = 0x0000FF
green = 0xFF0000

distances = range(5)[::-1]

def convertToLEDNum(toLight):
	return [toLight[i] * 10 - 6 for i in range(len(toLight))]

def clear():
        for i in range(numpixels):
                strip.setPixelColor(i, 0)

def update(toLight, dist, color):
	for center in toLight:
		strip.setPixelColor(center + 1 + dist, color)
		strip.setPixelColor(center - dist, color)
	strip.show();
	time.sleep(1.0/5)

clear()

print "chosen spots are: " + str(positionsToLight)
lightList = convertToLEDNum(positionsToLight)
print "converted to LED nums: " + str(lightList)

print "distances: "
for i in distances:
	update(lightList, i, red)
time.sleep(5 + (1.5 *  len(positionsToLight)))
for i in distances:
	update(lightList, i, off)
