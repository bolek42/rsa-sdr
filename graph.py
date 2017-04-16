import glob
import sys
import os

from config import *
from dsp import *
from dut import *

config_reload()

#config
f0 = config_get("capture.demod_frequency", int)
samp_rate = config_get("capture.demod_samp_rate", int)
fft_len =  config_get("preprocess.fft_len", int)
fft_step =  config_get("preprocess.fft_step", int)

res = np.load(args[0])
plot(   res,
        f0=f0,
        samp_rate=samp_rate,
        fft_step=fft_step,
        title="DES DPA",
        blocking=True,
        clear=False)

