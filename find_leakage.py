import numpy as np
from capture import capture
from dsp import *

ret = []
cap = capture()

center = 126e6
sr = 2e6
cap.capture_frequency = 126e6
cap.set_capture_frequency(126e6)

while True:
    challenges, trig, demod = cap.receive()
    response = cap.pulse_search(demod)
    ret += list(response.max(axis=0))

    plot(np.array(ret),f0=center, samp_rate=sr, blocking=False, clear=True)

    cap.set_capture_frequency(cap.capture_frequency + 2e6)
    center += 1e6
    sr += 2e6
