#!/data/data/com.termux/files/usr/bin/env python3

import threading
import socket
import time
import os
from nat import nat_traversal


LPORT = 0                    # 25276 corresponds 'alarm' on phone keyboard =)
LHOST = '0.0.0.0'
WAIT_FOR_KNOCK_TIME = 10        # Time to wait KNOCK before reporting about link loss
                                # This time should be at least 2 times greater, than
                                # KNOCK_DELAY in alarm_client.py

DIR_NAME = './alarm/' # Dirrectory, where sound files are
ALARM_FILE_NAME = 'alarm_short.mp3'
LINK_LOSS_FILE_NAME = 'link_loss.mp3'
LINK_RESTORE_FILE_NAME = 'link_restored.mp3'

KNOCK_FLAG = 0    # We will set this flag and wait for WAIT_FOR_KNOCK_TIME seconds
                  # if UDP packet with KNOCK will come before we wake up, this flag
                  # will be cleared by another thread

KNOCK_WARN = 1    # This flag is set when link is lost (KNOCK didn't come in time)
                  # We will use it to inform user about link restore

# we need a different thread to prevent lock while read from socket
class UDP_receive(threading.Thread):
    def run(self):
        global KNOCK_FLAG    # we will clear this flag when receive KNOCK
        while True:
            data, addr = sock.recvfrom(1024)    # read from socket
            if data == b'KNOCK\n':              # if KNOCK came
                print(data.decode('utf-8'), end = '')
                KNOCK_FLAG = 0                  # clear KNOCK_FLAG
                sock.sendto(b'OK\n', addr)       # response to server
            elif data == b'ALARM\n':              # if ALARM came, inform user about it immediately
                print(data.decode('utf-8'), end = '')
                sock.sendto(b'OK\n', addr)       # response to serve
                os.system('termux-media-player play ' + DIR_NAME + ALARM_FILE_NAME)
            else:
                print('Unknown data:')
                print(data.decode('utf-8'))

# prevent phone from sleeping
os.system('termux-wake-lock')

# create socket and bind it to LPORT
if LHOST and LPORT:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LHOST, LPORT))
else:
    RHOST, RPORT, sock = nat_traversal()

# start new thread to read from socket
thread = UDP_receive()
thread.start()

print('Starting alarm server... ')
while True:
    try:
        KNOCK_FLAG = 1                    # set KNOCK_FLAG (it should be cleared in another thread)
        time.sleep(WAIT_FOR_KNOCK_TIME )  # wait for WAIT_FOR_KNOCK_TIME seconds
        if KNOCK_FLAG:                    # check if KNOCK_FLAG was cleared by UDP_receive thread
            KNOCK_WARN = 1                # if not, inform user about link loss
            print('Связь потеряна')
            # os.system('termux-tts-speak ' + LINK_LOSS_MESSAGE)
            os.system('termux-media-player play ' + DIR_NAME +  LINK_LOSS_FILE_NAME)
        else:
            if KNOCK_WARN:                # else, if KNOCK_WARN was set, inform user about link restore
                KNOCK_WARN = 0            # and clear KNOCK_WARN flag
                print('Связь установлена')
                # os.system('termux-tts-speak ' + LINK_RESTORED_MESSAGE)
                os.system('termux-media-player play ' + DIR_NAME + LINK_RESTORE_FILE_NAME)

    except KeyboardInterrupt:
        break

sock.close()                      # close UDP socket
os.kill(thread._native_id, 15)    # didn't find a better way to stop UDP_receive thread
