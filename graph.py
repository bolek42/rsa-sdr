import glob
import sys
import os

from config import *
from dsp import *
from dut import *

config_reload()

#config
f0 = config_get("capture.frequency", int)
samp_rate = config_get("capture.samp_rate", int) / 8
fft_len =  config_get("preprocess.fft_len", int)
fft_step =  config_get("preprocess.fft_step", int)

#res = stft(res, 1024, 1024)
for f,c in zip(sys.argv[2:], ["#000000", "#666666"]):
    res = np.load(f)
    res = res[len(res)/2:]
    plot(   res,
            f0=samp_rate/4,
            samp_rate=samp_rate / 2,
            fft_step=fft_step,
            title="Demodulated",
            blocking=True,
            clear=False,
            color=c)

