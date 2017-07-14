import RPi.GPIO as GPIO
import time
import os


#os.system('aplay -N sound/Hightard.wav &')

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

for i in range(3):
    print i
    GPIO.output(17, True)
    time.sleep(.1)
    GPIO.output(17, False)
    time.sleep(.1)


led_state = True
GPIO.output(17, led_state)

while True:
    input_state = GPIO.input(18)
    if input_state ==False:
        print('Button Pressed')
        led_state = not led_state
        GPIO.output(17, led_state)
        os.system('aplay -N sound/Cloistr.wav &')
        time.sleep(1)

GPIO.cleanup()
