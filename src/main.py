#!/usr/bin/python
import time
import shelve
import os.path
import Adafruit_DHT
import RPi.GPIO as GPIO

from flask import request
from flask_api import FlaskAPI


class characteristic:
  '''
  Represents a characteristic for the tower fan.
  '''

  def __init__(self, characteristic, gpio_pin, display_name):
    self.characteristic = characteristic
    self.gpio = gpio_pin
    self.name = display_name


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

  if characteristic.characteristic == 'SwingMode':
    setRelayStateForGPIOToValue(characteristic.gpio, value)
  elif characteristic.characteristic == 'RotationSpeed':
    resetFanSpeed()
    setRelayStateForGPIOToValue(characteristic.gpio, 1)
  elif characteristic.characteristic == 'Active':
    clearFanSpeed()

  persistValueforCharacteristic(value, characteristic)


def persistValueforCharacteristic(value, characteristic):
  '''
  Writes the value for the given characteristic to the store.
  '''

  store = shelve.open(data_store)
  store[characteristic.characteristic] = value
  store.close()


def clearFanSpeed():
  '''
  Sets the relay state to 0 for all fan speeds. Clearing the fan
  speed is equivalent to turning the fan off.
  '''

  setRelayStateForGPIOToValue(charSpeedOne.gpio, 0)
  setRelayStateForGPIOToValue(charSpeedTwo.gpio, 0)
  setRelayStateForGPIOToValue(charSpeedThree.gpio, 0)


def setRelayStateForGPIOToValue(gpio, value):
  '''
  Sets the GPIO pin to LOW or HIGH based on the provided relay
  state value.
  '''

  if value == 1:
    GPIO.output(gpio, GPIO.HIGH)
  elif value == 0:
    GPIO.output(gpio, GPIO.LOW)


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

  current_active = getCharacteristicValueFor(charActive)
  return {'response': current_active}


@app.route('/setActive', methods=["POST"])
def setActive():
  '''
  Sets the requested Active value. Setting the active will not affect
  the fan's swing mode.
  '''

  acceptable_values = [0, 1]
  value = int(request.args['Active'])

  if value in acceptable_values:
    setCharacteristicValueFor(charActive, value)
    return {'response': 200}
  else:
    return {'response': 400}


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

  current_swing_mode = getCharacteristicValueFor(charSwingMode)
  return {'response': current_swing_mode}


@app.route('/setSwingMode', methods=["POST"])
def setSwingMode():
  '''
  Sets the requested Swing Mode value
  '''

  acceptable_values = [0, 1]
  value = int(request.args['SwingMode'])

  if value in acceptable_values:
    setCharacteristicValueFor(charActive, value)
    return {'response': 200}
  else:
    return {'response': 400}


'''
API: Rotation Speed
Method: GET, POST
Usage: Represents the speed at which the fan is spinning
'''

@app.route('/getRotationSpeed', methods=["GET"])
def getRotationSpeed():
  '''
  Returns the current Swing Mode value
  '''

  current_swing_mode = getCharacteristicValueFor(charSpeedOne)
  return {'response': current_swing_mode}


@app.route('/setRotationSpeed', methods=["POST"])
def setRotationSpeed():
  '''
  Sets the requested Swing Mode value
  '''

  acceptable_values = range(101)
  value = int(request.args['RotationSpeed'])

  if value in acceptable_values:
    if 0 <= value <= 33:
      setCharacteristicValueFor(charSpeedOne, value)
    elif 34 <= value <= 66:
      setCharacteristicValueFor(charSpeedTwo, value)
    elif 67 <= value <= 100:
      setCharacteristicValueFor(charSpeedThree, value)
    return {'response': 200}
  else:
    return {'response': 400}


'''
API: Current Temperature
Method: GET
Usage: Represents current temperature for the sensor
'''

@app.route('/getCurrentTemperature', methods=["GET"])
def getCurrentTemperature():
  '''
  Returns the current temperature value
  '''

  humidity, temperature = Adafruit_DHT.read_retry(sensor_temperature, pin_temperature)
  return {'response': temperature}


'''
API: Humidity
Method: GET
Usage: Represents current humidity reading for the sensor
'''

@app.route('/getCurrentRelativeHumidity', methods=["GET"])
def getCurrentRelativeHumidity():
  '''
  Returns the current temperature value
  '''

  humidity, temperature = Adafruit_DHT.read_retry(sensor_temperature, pin_temperature)
  return {'response': humidity}


'''
API: Shutdown
Method: GET
Usage: Safely shutdown server and Raspberry Pi
'''

@app.route('/shutdown', methods=['POST'])
def shutdown():
  '''
  Safely shuts down Flask server and clears GPIO
  '''

  func = request.environ.get('werkzeug.server.shutdown')
  if func is None:
      raise RuntimeError('Not running with the Werkzeug Server')
  GPIO.cleanup()
  func()
  return 'Server shutting down...'


# Configure GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT) # Fan Speed 1
GPIO.setup(13, GPIO.OUT) # Fan Speed 2
GPIO.setup(15, GPIO.OUT) # Fan Speed 3
GPIO.setup(16, GPIO.OUT) # Fan Oscillation


# Configure Temperate Sensor
pin_temperature = 4 # Adafruit uses BCM numbering Board Pin 7
sensor_temperature = Adafruit_DHT.DHT22

# Define Fan Characteristics
charSwingMode = characteristic('SwingMode', 11, 'Swing Mode')
charActive = characteristic('Active', 0, 'Active')
charSpeedOne = characteristic('RotationSpeed', 13, 'Low')
charSpeedTwo = characteristic('RotationSpeed', 15, 'Medium')
charSpeedThree = characteristic('RotationSpeed', 16, 'High')

# Configure Paths
path_to_dir = os.path.dirname(os.path.abspath(__file__))
path_to_store = os.path.join(path_to_dir, 'store.db')
data_store = os.path.join(path_to_dir, 'store')


if __name__ == "__main__":

  initialize()
  app.run(host='0.0.0.0', port=80)
