#!/usr/bin/env python

from random import shuffle, choice, getrandbits
import numpy as np
import socket
import glob
import imp
import sys
import os
import threading

from config import config_get, config_reload
from dsp import *
from dut import *
from dpa import *
import dpa as dpalib

def n2hex(n, length=512):
    res = ""
    while n > 0:
        res = "%02x" % (n%256) + res
        n /= 256

    res = ("0"*(length - len(res))) + res
    return res


def attack(runs=60, N=2048):
    global n1, p1, d1, n2, p2, d2, n, p, d, bit, m, m1, ref
    dpa = dpalib.dpa()

    f1,f2,t1,t2 = 0.0001, 0.45, 0.505, 0.405

    #r will always perform a reduction
    r = n2hex(2**(N-1) + 2**(N-2) + 2**(N-3) + 2**(N-4) + 2**(N-5) + 2**(N-6) + 2**(N-7) + 2**(N-8) )

    #reduction
    values = [n2hex(2**(N-1) + 2**(N-8)), r]
    n2,p2 = dpa.oracle(verbose=False, values=values, runs=runs*2)
    d2  = p2 - n2

    #no reduction
    values = [n2hex(2**(N-1) + 2**(N-8)), n2hex(2**(N-1) + 2**(N-9))]
    n1,p1 = dpa.oracle(verbose=True, values=values, runs=runs*2, max_trace=runs)
    d1  = p1 - n1
    

    m =  2**(N-1)
    ref = 2**(N-1) + 2**(N-8)
    bit = N-2
    while bit > 1:
        m1 = m + (2 ** bit) #+ getrandbits(bit-64)
        values = [n2hex(ref), n2hex(m1)]
        n,p = dpa.oracle(verbose=False, values=values, max_trace=runs, runs=runs*2)

        d = p - n

        if np.abs(d-d1) < np.abs(d-d2):
            m = m1
            ref = m

        bit -= 1

n1 = p1 = d1 = n2 = p2 = d2 = n = p = d = bit = m = m1 = ref = 0
start = time.time()
def show_state():
    global n1, p1, d1, n2, p2, d2, n, p, d, bit, m, m1, ref
    t = time.time()-start
    sys.stderr.write( "\x1b[0;0H"+"\x1b[2J"+"\r")
    sys.stderr.write( "Elapsed time %dm %ds\n" % (t/60,t%60))
    sys.stderr.write( "Current Bit %d\n" % bit)
    sys.stderr.write( "Known Modul: %s...\n" % n2hex(m)[:64])
    sys.stderr.write( "Challenge: %s...\n\n" % n2hex(m + (2 ** bit))[:64])

    sys.stderr.write( "No Reduction:\t%f-(%f) = %f\n" % ( p1,n1,d1))
    sys.stderr.write( "Reduction:\t%f-(%f) = %f\n" % ( p2,n2,d2))
    sys.stderr.write( "Last Bit:\t%f-(%f) = %f\n" % ( p,n,d))

    if d1 > 0 and d2 > 0:
        if np.abs(d-d1) < np.abs(d-d2):
            sys.stderr.write( "Last Bit was 1\n")
        else:
            sys.stderr.write( "Last Bit was 0\n")

    sys.stderr.write( "\n" + "#" * 0x42 + "\n")
    threading.Timer(0.1, show_state).start()
show_state()

try:
    attack()
except:
    import traceback; traceback.print_exc()
    os.kill(os.getpid(), 9) #suicide to kill all threads
