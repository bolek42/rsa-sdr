import glob
import sys
import os

from config import *
from dsp import *
from dut import *

config_reload()

#config
f0 = 0#config_get("capture.frequency", int)
samp_rate = 0#config_get("capture.samp_rate", int) / 8
fft_len =  0#config_get("preprocess.fft_len", int)
fft_step =  0#config_get("preprocess.fft_step", int)

print args[0]
res = np.load(args[0])
plot(   res,
        f0=samp_rate/4,
        samp_rate=samp_rate / 2,
        fft_step=fft_step,
        title="Demodulated",
        blocking=True,
        clear=False)

