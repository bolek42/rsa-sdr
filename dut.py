#!/usr/bin/env python

import socket
import time
import subprocess
from random import getrandbits
from config import config_get, config_reload

from config import *

def n2hex(n, length=512):
    res = ""
    while n > 0:
        res = "%02x" % (n%256) + res
        n /= 256

    res = ("0"*(length - len(res))) + res
    return res

VALUES = {  "./cprog/openssl-mul-4096":
                #[ n2hex(getrandbits(4095)), n2hex(getrandbits(4095))],
                [ n2hex(getrandbits(4095)), n2hex(2**4094+2**4094+2**4000)],

            "./cprog/openssl-mul":
                #[ n2hex(getrandbits(2047)), n2hex(getrandbits(2047))],
                [ n2hex(getrandbits(2047)), n2hex(2**2047+2**2046)],

            "./cprog/openssl-mul-mont":
                #[ n2hex(2**2047+2**2045), n2hex(2**2047+2**2046)],
                [ n2hex(2**2047+2**2046+2**2045), n2hex(2**2047+2**2046)],
            "./cprog/openssl-exp" :
                #2^n
                #[ n2hex(getrandbits(2046)), n2hex(2**2047)],
                #[ n2hex(getrandbits(2046)), n2hex(getrandbits(2046))],

                #reduction
                #[   n2hex(2**2047 + 2**2042),
                #    n2hex(2**2047 + 2**2041)],
                [   n2hex(2**2047 + 2**2042),
                    n2hex(2**2047 + 2**2046 + 2**2045 + 2**2044 + 2**2043)],

                #both
                #[   n2hex(2**2047 + 2**2046 + 2**2045 + 2**2044 + 2**2043 + getrandbits(2042)),
                #    n2hex(2**2047 + 2**2046 + 2**2043 + getrandbits(2042))],#+ 2**2044)],
                #[   n2hex(2**2047 + 2**2046 + 2**2045 + 2**2044 + 2**2043 + getrandbits(2042)),
                #    n2hex(2**2047 + 2**2046 + 2**2045 + 2**2044 + 2**2043 + getrandbits(2042))],
            "./cprog/openssl-exp-bin" :
                #both
                [   n2hex(2**2047 + 2**2046 + 2**2045 + 2**2044 + 2**2043 + getrandbits(2042)),
                    n2hex(2**2047)],
                #[   n2hex(2**2047 + 2**2046 + 2**2045 + 2**2044 + 2**2043 + getrandbits(2042)),
                #    n2hex(2**2047 + 2**2046 + 2**2045 + 2**2044 + 2**2043 + getrandbits(2042))],

            "./cprog/openssl-exp-4096" :
                [   n2hex(2**4095 + 2**4094 + 2**4093 + 2**4092 + 2**4091 + getrandbits(4090)),
                    n2hex(2**4095 + 2**4094)],

            "./cprog/openssl-exp-bin-4096" :
                [   n2hex(2**4095 + 2**4094 + 2**4093 + 2**4092 + 2**4091 + getrandbits(4090)),
                    n2hex(2**4095)]
        }

class dut():
    def __init__(self):
        self.apply_config()
        self.connect()

    def apply_config(self):
        global VALUES
        config_reload()
        self.cmd = config_get("misc.cmd", str)
        self.ip = config_get("misc.ip", str)
        self.port = config_get("misc.port", int)
        self.values = VALUES[self.cmd]

    def connect(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.ip, self.port))
        self.s = s

    def reconnect(self):
        self.s.close()
        self.connect()

    def challenge(self, challenge):
        self.s.send("%s %s" % (self.cmd, str(challenge)))
        response = self.s.recv(1024)

class dut_service():
    def __init__(self):
        self.apply_config()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", self.port))
        s.listen(1)
        s.setblocking(1)
        self.s = s

    def apply_config(self):
        config_reload()
        self.port = config_get("misc.port", int)

    def run(self):
        while True:
            conn, addr = self.s.accept()
            try:
                while True:
                    request = conn.recv(4096)
                    if not request: break

                    response = self.work(request)
                    conn.send(response)

                conn.close()
            except socket.error:
                pass

    def work(self, challenge):
        cmd = challenge.split(" ")
        if cmd[0] in VALUES:
            #print "calling: %s" % " ".join(cmd)
            subprocess.call(cmd)

        return "ok"


if __name__ == "__main__":
    d = dut_service()
    d.run()
