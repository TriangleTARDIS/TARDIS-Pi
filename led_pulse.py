import RPi.GPIO as GPIO
import time


print "Go..."
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT)
GPIO.output(11, False)
time.sleep(1)

p = GPIO.PWM(11, 200)
p.start(0)

try:
 fs = 0.009
 while True:
  print "Up"
  for i in range(100):
   p.ChangeDutyCycle(i)
   time.sleep(fs)

  print "Down"
  for i in range(100):
   p.ChangeDutyCycle(100 - i)
   time.sleep(fs)

 #p.ChangeFrequency(100)
 p.stop()

except Exception as e:
 print("Failed")
 print(e)
 GPIO.cleanup()
 pass

finally:
 GPIO.cleanup()
