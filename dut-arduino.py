#!/usr/bin/env python

import sys
import time
import subprocess
import serial #pyserial
from random import getrandbits
from binascii import unhexlify

import time

class dut():
    test_value = "0011223344556677"
    key = "deadbeefdeadbeef"

    def __init__(self):
        self.serial = serial.Serial('/dev/ttyACM0', 115200)
        time.sleep(1)


    def challenge(self, challenge):
        if len(unhexlify(challenge)) != 8:
            print "invalid plain text %s" % challenge
            sys.exit(1)
        self.serial.write(unhexlify(self.key))
        self.serial.write(unhexlify(challenge))
        cipher = self.serial.read(8)
        return cipher

if __name__ == "__main__":
    d = dut()
    t = time.time()
    while True:
        d.challenge("0011223344556677")
        if time.time() - t > 1:
            time.sleep(2)
            t = time.time()
