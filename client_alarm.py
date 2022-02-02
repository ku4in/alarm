#!/data/data/com.termux/files/usr/bin/env python3

import socket
import json
from subprocess import Popen, PIPE
import os
import time
from nat import nat_traversal


AVERAGE = 10                    # Number of measures of acceleration to average 
KNOCK_DELAY = 5                 # Delay between knocks to servers in seconds
SENSOR_NAME = 'ACCELEROMETER'   # Use 'termux-sensor -l' command to get particular sensor name in your phone
ACCELEROMETER_DELAY = 20        # Delay between measurements (ms)
ACCELERATION_THRESHOLD = 0.1    # If acceleration differance square exceed this value the alarm signal will be sent
DELAY_AFTER_ALARM = 1           # Delay after motion detection (s) (to prevent multiple alarm send)
RPORT = 0                        # Port to knock to
RHOST = ''                # Host to knock to


def sensor_get():
    # read json structure from stdout of 'p' (it has 9 lines)
    one_measure = ''
    while not one_measure:                              # skip blank output of termux-sensor ({})
        for i in range(9):
           one_measure += p.stdout.readline().decode('utf-8')
           if one_measure == '{}\n':                    # sometimes termux-sensor returns nothing ({})
               one_measure = ''                         # in that case just crear one_measure value for future read
               break                                    # break to begin 9 lines count
        if one_measure:                                 # if we got a measurement
            data = json.loads(one_measure)              # make dict from json
            a = data[SENSOR_NAME]['values']         # get acceleration from dict
    return a

# prevent phone from sleeping
os.system('termux-wake-lock')

# create a UDP socket
if RHOST and RPORT:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
else:
    RHOST, RPORT, sock = nat_traversal()

# Perform cleanup
# to prevent stuck of sensor
os.system('termux-sensor -c')

# acceleration sensor polling process
p = Popen(['/data/data/com.termux/files/usr/bin/termux-sensor', '-s', SENSOR_NAME, '-d', str(ACCELEROMETER_DELAY)],\
    stdin=PIPE, stdout=PIPE)

# initialize acceleration and time
a_prev = sensor_get()
print('sensor ready!')
t_prev = time.time()

while True:
    try:
        acceleration = 0
        # average the measured acceleration values
        for i in range(AVERAGE):
            a = sensor_get()
            # calculate acceleration square as differance between current components and previous ones
            da = sum( (ai - a_prev_i)**2 for ai, a_prev_i in zip(a, a_prev))
            # add this differanse to acceleration for future average
            acceleration += da
            a_prev = a
        # average acceleration
        acceleration /= AVERAGE
        # if acceleration is greater than threshold, then send alarm signal and sleep for DELAY_AFTER_ALARM time
        if acceleration > ACCELERATION_THRESHOLD:
            sock.sendto(b'ALARM\n', (RHOST, RPORT))
            print('ALARM')
            time.sleep(DELAY_AFTER_ALARM)
        # get current time to calqulate how long ago we knocked to server
        t_cur = time.time()
        # if we knocked more then KNOCK_DELAY seconds ago, knock again
        if t_cur - t_prev > KNOCK_DELAY:
            sock.sendto(b'KNOCK\n', (RHOST, RPORT))
            print('KNOCK')
            t_prev = t_cur
    except KeyboardInterrupt:
        # Here we can handle other errors, e.g. Network unreacheble
        break
p.send_signal(2)
sock.close()
