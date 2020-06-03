#!/usr/bin/python
import time
import shelve
import os.path
import RPi.GPIO as GPIO

from flask import request
from flask_api import FlaskAPI


# Configure Servos
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT)
servo1 = GPIO.PWM(11,50)
servo1.start(0)

# Configure Paths
path_to_dir = os.path.dirname(os.path.abspath(__file__))
path_to_store = os.path.join(path_to_dir, 'store.db')
data_store = os.path.join(path_to_dir, 'store')


def initialize():
  '''
  Initializes system by creating data store, setting default values 
  and setting the current values.
  '''

  initialize_store()


def initialize_store():
  '''
  Creates a data store and sets default values when one is not found.
  '''

  does_file_exist = os.path.isfile(path_to_store)

  if does_file_exist == False:
    print('Creating Datastore...')
    default_active = 0
    default_swing_mode = 0
    default_rotation_speed = 0
    store = shelve.open(data_store)
    store['Active'] = default_active
    store['SwingMode'] = default_swing_mode
    store['RotationSpeed'] = default_rotation_speed
    store.close()


def getCharacteristicValueFor(characteristic):
  '''
  Returns the current stored value for requested characteristic
  '''

  store = shelve.open(data_store)
  current_value = store[characteristic]
  store.close()

  return current_value


def setCharacteristicValueFor(characteristic, value):
  '''
  Stores the current stored value for requested characteristic
  '''

  store = shelve.open(data_store)
  store[characteristic] = value
  store.close()


def setServoAngle(angle):
  '''
  Sets the servo to requested angle
  '''

  servo1.ChangeDutyCycle(2+(angle/18))
  time.sleep(0.5)
  servo1.ChangeDutyCycle(0)


#############
# FLASK API #
#############

app = FlaskAPI(__name__)

'''
API: Active
Method: GET, POST
Usage: Represents the On/Off state of the Fan
'''

@app.route('/getActive', methods=["GET"])
def getActive():
  '''
  Returns the current Active value
  '''

  current_active = getCharacteristicValueFor('Active')
  return {'response': current_active}


@app.route('/setActive', methods=["POST"])
def setActive():
  '''
  Sets the requested Active value
  '''

  value = int(request.args['Active'])

  if value == 1:
    print("Turning on fan")
  elif value == 0:
    print("Turning off fan")

  setCharacteristicValueFor('Active', value)

  return {'response': 200}


'''
API: Swing Mode
Method: GET, POST
Usage: Represents the On/Off state of the Fan's oscillation
'''

@app.route('/getSwingMode', methods=["GET"])
def getSwingMode():
  '''
  Returns the current Swing Mode value
  '''

  current_swing_mode = getCharacteristicValueFor('SwingMode')
  return {'response': current_swing_mode}


@app.route('/setSwingMode', methods=["POST"])
def setSwingMode():
  '''
  Sets the requested Swing Mode value
  '''

  value = int(request.args['SwingMode'])

  if value == 1:
    print("Turning on swing mode")
    setServoAngle(120)
  elif value == 0:
    print("Turning off swing mode")
    setServoAngle(0)

  setCharacteristicValueFor('SwingMode', value)

  return {'response': 200}


'''
API: Shutdown
Method: GET
Usage: Safely shutdown server and Raspberry Pi
'''

@app.route('/shutdown', methods=['POST'])
def shutdown():
  '''
  Safely shuts down Flask server and GPIO
  '''

  func = request.environ.get('werkzeug.server.shutdown')
  if func is None:
      raise RuntimeError('Not running with the Werkzeug Server')
  servo1.stop()
  GPIO.cleanup()
  func()
  return 'Server shutting down...'


if __name__ == "__main__":

  initialize()
  app.run(host='0.0.0.0', port=80)
