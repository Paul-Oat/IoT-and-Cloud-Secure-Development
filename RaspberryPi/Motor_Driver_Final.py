#Libary Imports
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from datetime import datetime
import RPi.GPIO as GPIO
import fcntl
import ctypes
import time
import json


# AWS MQTT ###############################################################
endpoint = ""  # AWS IoT endpoint
rootCAPath = ""  # Root CA certificate
certPath = ""  # Device certificate
keyPath = ""  # Private key

topic = "rpi_Car/control"  # MQTT topic


myMQTTClient = AWSIoTMQTTClient("RPI_data")
myMQTTClient.configureEndpoint(endpoint, 8883)
myMQTTClient.configureCredentials(rootCAPath, keyPath, certPath)
myMQTTClient.configureOfflinePublishQueueing(-1)
myMQTTClient.configureDrainingFrequency(2)  
myMQTTClient.configureConnectDisconnectTimeout(20)  
myMQTTClient.configureMQTTOperationTimeout(10)  
myMQTTClient.connect() #Connect to the MQTT stream

#lkm #####################################################################
IOCTL_PIIO_GPIO_READ = 0x67 # IOCTL code 
IOCTL_PIIO_GPIO_WRITE = 0x68 # IOCTL code 
fd = open("/dev/piiodev") #LKM path

#C-type Structure  
class GPIO_Struct(ctypes.Structure):
		_fields_ = [("desc", ctypes.c_char * 16),
			("pin", ctypes.c_uint),
				("value", ctypes.c_int),
				("opt", ctypes.c_char)]

#indicator 
def toggle_gpio(pinVal):
	times = 7
	for i in range(times):
		ret = fcntl.ioctl(fd, IOCTL_PIIO_GPIO_WRITE, pinVal)
		
		# invert
		pinVal.value = not pinVal.value


		time.sleep(0.5)
		i = i + 1 
	pinVal.value = 0
	ret = fcntl.ioctl(fd, IOCTL_PIIO_GPIO_WRITE, pinVal)

#####################################################################
#motor servo /////
class Motor(object):

	_DEBUG = False
	_DEBUG_INFO = 'DEBUG "TB6612.py":'

	def __init__(self, direction_channel, pwm=None, offset=True):
		'''Init MotorA motor on giving dir. channel and PWM channel.'''
		self._debug_("Debug on")
		self.direction_channel = direction_channel
		self._pwm = pwm
		self._offset = offset
		self.forward_offset = self._offset

		self.backward_offset = not self.forward_offset
		self._speed = 0

		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BOARD)

		self._debug_('setup motor direction channel at %s' % direction_channel)
		self._debug_('setup motor pwm channel')# self._debug_('setup motor pwm channel as %s ' % self._pwm.__name__)
		GPIO.setup(self.direction_channel, GPIO.OUT)

	def _debug_(self,message):
		if self._DEBUG :
			print(self._DEBUG_INFO,message)

	@property
	def speed(self):
		return self._speed

	@speed.setter
	def speed(self, speed):
		''' Set Speed with giving value '''
		if speed not in range(0, 101):
			raise ValueError('speed ranges fron 0 to 100, not "{0}"'.format(speed))
		if not callable(self._pwm):
			raise ValueError('pwm is not callable, please set Motor.pwm to MotorA pwm control function with only 1 veriable speed')
		self._debug_('Set speed to: %s' % speed)
		self._speed = speed
		self._pwm(self._speed)

	def forward(self):
		''' Set the motor direction to forward '''
		GPIO.output(self.direction_channel, self.forward_offset)
		self.speed = self._speed
		self._debug_('Motor moving forward (%s)' % str(self.forward_offset))

	def backward(self):
		''' Set the motor direction to backward '''
		GPIO.output(self.direction_channel, self.backward_offset)
		self.speed = self._speed
		self._debug_('Motor moving backward (%s)' % str(self.backward_offset))

	def stop(self):
		''' Stop the motor by giving MotorA 0 speed '''
		self._debug_('Motor stop')
		self.speed = 0

	@property
	def offset(self):
		return self._offset

	@offset.setter
	def offset(self, value):
		''' Set offset for much user-friendly '''
		if value not in (True, False):
			raise ValueError('offset value must be Bool value, not"{0}"'.format(value))
		self.forward_offset = value
		self.backward_offset = not self.forward_offset
		self._debug_('Set offset to %d' % self._offset)

	@property
	def debug(self, debug):
		return self._DEBUG

	@debug.setter
	def debug(self, debug):
		''' Set if debug information shows '''
		if debug in (True, False):
			self._DEBUG = debug
		else:
			raise ValueError('debug must be "True" (Set debug on) or "False" (Set debug off), not "{0}"'.format(debug))

		if self._DEBUG:
			print(self._DEBUG_INFO, "Set debug on")
		else:
			print(self._DEBUG_INFO, "Set debug off")

	@property
	def pwm(self):
		return self._pwm

	@pwm.setter
	def pwm(self, pwm):
		self._debug_('pwm set')
		self._pwm = pwm

	  



# try to set up gpio and PWM for the motors and servo
try:
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup((35, 32, 12), GPIO.OUT)
	GPIO.setup((36), GPIO.OUT)
	MotorA = GPIO.PWM(12, 60)
	MotorB = GPIO.PWM(32, 60)
	time.sleep(1)
	Servo = GPIO.PWM(35, 50)
	MotorA.start(0)
	MotorB.start(0)
	Servo.start(0)
except Exception as e:
	#else disclose the error
	print(f"An error occurred: {e}")

#set the speed of motor A
def a_speed(value):
	MotorA.ChangeDutyCycle(value)
#set the speed of motor B
def b_speed(value):
	MotorB.ChangeDutyCycle(value)

#set the front servo angle between 2.5 and 12 
def servo_angle(value):
	if value >= 2.5 and value <= 12:
		Servo.ChangeDutyCycle(value)
		#fuzzy logic here exact number would be 6.75
		if value <= 5:
			toggle_gpio(pinL)
		elif value >= 8:
			toggle_gpio(pinR)    
		print("changed Servo angle")
		time.sleep(1)

#motor setup
motorA = Motor(11) 
motorB = Motor(10)
motorA.debug = True
motorB.debug = True
motorA.pwm = a_speed
motorB.pwm = b_speed
delay = 0.05
servoVal = 8 
origservoVal = 8


#LKM pins
pinL = GPIO_Struct()
pinR = GPIO_Struct()

pinL.pin= 22
pinR.pin = 27
data = ""


#logic function 
def control(client, userdata, message):

	#Get the payload
	data = message.payload
	print("In control loop")
	#try to get the values from the MQTT stream
	try:
		#debug statement
		#print("In try")
		#print(data)

		if(data != ""):
			print(data)
			
			#get data speed and direction from var

			data = json.loads(data)
			speed = int(data.get("Speed", ""))
			direction = data.get("Direction", "")
			servoVal = float(data.get("Wheel Angle", ""))

			#if Time difference exists then 
			if 'TimeDifference' in data:
				#debug 
				##print("Database instruction")
				
				#if previous time is present
				if time_previous != "":
					#get current time 
					time_current = item.get('TimeDifference')
					dt1 = datetime.strptime(time_current, "%a, %d %b %Y %H:%M:%S +0000")
					dt2 = datetime.strptime(time_previous, "%a, %d %b %Y %H:%M:%S +0000")

					#compare the difference
					time_difference = dt1 - dt2
				else:
				#if time is not present 
				#set fur further iteration
				#sleep for no time
					time_previous = item.get('TimeDifference')
					time_difference = 0
				time.sleep(timeDifference)

			else:
				#debug
				print("Normal instruction")
			#debug
			#print(data)
			#print(speed)
			#print(direction)
			#print(servoVal)
			
			#if current servo is not equal to orginal servo val
			if (servoVal != origservoVal):
				#set servo angle
				servo_angle(servoVal)
			#f direction given is forward
			if direction == 'forward':
				#debug
				#print("Going forward")
				#set motor forward
				motorA.forward()
				motorB.forward()
				#set the speed
				motorA.speed = speed
				motorB.speed = speed
			#if direction is backwards
			elif direction == 'backward':
				#debug
				#print("going backwards")
				#set motor backward
				motorA.backward()
				motorB.backward()
				#set the speed
				motorA.speed = speed 
				motorB.speed = speed
			else:
				#debug 
				print("I give up now")

	#if CTRL + C is pressed
	except KeyboardInterrupt:
		#debug
		print("Cleanup")
		#pass to clean up functions
		pass
		myMQTTClient.unsubscribe(topic)
		myMQTTClient.disconnect()
		GPIO.cleanup()
		fd.close()

#####################################################################

#application entry. 
if __name__ == '__main__':
	while True:
		#MQTT function fetch control loop
		myMQTTClient.subscribe(topic, 1, control)
