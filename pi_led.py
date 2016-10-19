 #actual file is on pi
 
 #!/usr/bin/python
  2 import sys
  3 import time
  4 from dotstar import Adafruit_DotStar
  5 
  6 arg1 = sys.argv[1]
  7 ledNum = int(arg1)
  8 
  9 # Here's how to control the strip from any two GPIO pins:
 10 datapin   = 10
 11 clockpin  = 11
 12 numpixels = 117
 13 strip     = Adafruit_DotStar(numpixels, datapin, clockpin)
 14 
 15 strip.begin()           # Initialize pins for output
 16 strip.setBrightness(64) # Limit brightness to ~1/4 duty cycle
 17 
 18 red = 0x00FF00
 19 blue = 0x0000FF
 20 green = 0xFF0000
 21 
 22 def clear():
 23         for i in range(numpixels):
 24                 strip.setPixelColor(i, 0)
 25 
 26 
 27 def spread(center, distance, color):
 28         #strip.setPixelColor(center, color)
 29 
 30         for i in reversed(range(distance)):
 31                 #strip.setPixelColor(center, color)
 32                 strip.setPixelColor(center + i, color)
 33                 strip.setPixelColor(center - i, color)
 34                 strip.show()
 35                 time.sleep(1.0 / 5)
 36 
 37         time.sleep(3)
 38 
 39         #strip.setPixelColor(center, 0)
 40         for i in reversed(range(distance)):
 41                 strip.setPixelColor(center + i, 0)
 42                 strip.setPixelColor(center - i, 0)
 43                 strip.show()
 44                 time.sleep(1.0 / 5)
 45 
 46 
 47 
 48 """
 49 strip.setPixelColor(ledNum, 0xFFFFFF)
 50 strip.show()
 51 
 52 time.sleep(5)
 53 
 54 strip.setPixelColor(ledNum, 0)
 55 strip.show()
 56 """
 57 
 58 clear()
 59 spread(ledNum, 5, blue)
 60 quit()
 
