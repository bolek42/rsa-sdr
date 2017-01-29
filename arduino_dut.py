#!/usr/bin/env python

import socket
import time
import subprocess
import serial #pyserial
from random import getrandbits
from config import config_get, config_reload

from config import *
import time

def n2hex(n, length=512):
    res = ""
    while n > 0:
        res = "%02x" % (n%256) + res
        n /= 256

    res = ("0"*(length - len(res))) + res
    return res


# DUT client
class dut():
    def __init__(self):
        self.serial = serial.Serial('/dev/ttyACM0', 115200)
        self.values = ["\x00\x11\x22\x33\x44\x55\x66\x77"]
        time.sleep(1)


    def challenge(self, challenge):
        self.serial.write("\xde\xad\xbe\xef\xde\xad\xbe\xef") #key
        self.serial.write(challenge) #plain
        cipher = self.serial.read(8)
        return cipher

    

if __name__ == "__main__":
    d = dut()
    while True:
        d.challenge("\x00\x11\x22\x33\x44\x55\x66\x77")
