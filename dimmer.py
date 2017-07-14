import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
GPIO.setup(29, GPIO.OUT)
GPIO.setup(31, GPIO.OUT)
GPIO.setup(33, GPIO.OUT)
GPIO.setup(35, GPIO.OUT)

print "DEFAULT"
GPIO.output(29, False)
GPIO.output(31, False)
GPIO.output(33, False)
GPIO.output(35, False)

levels = [15, 7, 6, 5, 4, 11, 10, 12, 13, 9, 8, 3, 2, 1, 14, 0]
levels = [15, 7, 6, 5, 4, 11, 10, 9, 8, 3, 2, 1, 0]
sleep = .05

while True:
   for n in range(len(levels)):
      i = levels[n]
      print "N: ", n
      #print "I: ", i
      #print "I: ", i & 1 ==1, i & 2==2, i&4==4, i&8==8
      GPIO.output((29, 31, 33, 35), (i & 1==1, i & 2 ==2, i & 4 == 4, i & 8 == 8))
      time.sleep(sleep)

   for n in range(len(levels)-1,0,-1):
      i = levels[n]
      print "N: ", n
      #print "I: ", i
      #print "I: ", i & 1 ==1, i & 2==2, i&4==4, i&8==8
      GPIO.output((29, 31, 33, 35), (i & 1==1, i & 2 ==2, i & 4 == 4, i & 8 == 8))
      time.sleep(sleep)

#while True:
#   i = int(raw_input("I:"))
#   print "I: ", i
#   print "I: ", i & 1 ==1, i & 2==2, i&4==4, i&8==8
#   GPIO.output((29, 31, 33, 35), (i & 1==1, i & 2 ==2, i & 4 == 4, i & 8 == 8))

GPIO.cleanup()
