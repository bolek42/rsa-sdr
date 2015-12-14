import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from multiprocessing import Process
import time

# Fourier & Co.
def stft(trace, fft_len=1024, fft_step=2048, n_fft=0, log=True):
    if n_fft == 0:
        n_fft = np.ceil( (len(trace) - fft_len) / fft_step + 1)

    # Verschiebe das Fenster ueber die Spur
    frames = np.lib.stride_tricks.as_strided(   trace, 
                                shape=(n_fft, fft_len),
                                strides=(trace.strides[0]*fft_step,
                                trace.strides[0])).copy()

    # Anwendung der FFT auf die Spur
    frames *= np.blackman(fft_len)
    stft = np.fft.fft(frames)
    stft = map(lambda fft: np.append(fft[fft_len/2:],fft[:fft_len/2]), stft)
    stft = np.abs(stft)
    if log:
        stft = np.log10(stft)

    return stft

def stft_bin2f(b, f0, fft_len, samp_rate):
    b = float(b)
    return f0 + ((b / fft_len) - 0.5) * samp_rate

def stft_f2bin(f, f0, fft_len, samp_rate):
    f = float(f)
    return int(fft_len * (((f - f0) / samp_rate) + 0.5) + 0.5)

# cfile File handler (GNURadio file format)
def load(filename, count=-1):
    return np.fromfile(filename, dtype=np.dtype('c8'), count=1)

def save(array, filename):
    try:
        array.tofile(filename)
    except AttributeError:
        pass

# graphing data
def plot(   data,
            samp_rate=1,
            fft_step=1,
            f0=0,
            blocking=True,
            clear=True,
            png="/tmp/plot.png",
            npy="/tmp/plot",
            title="",
            xlabel="Time in ms",
            ylabel="Frequency in MHz",
            color='k'):

    #arch show thread hack
    global p
    if p is not None:
        p.terminate()
        p.join()

    if clear:
        plt.clf()

    if data is None:
        return

    matplotlib.rcParams.update({'font.size': 18})

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    #1D Graphs
#    if len(data.shape) == 1:
#        if samp_rate > 1:
#            x = np.arange(0,len(data)/float(samp_rate), 1.0/samp_rate)
#            x *= 1e3
#            x = x[:len(data)]
#            plt.plot(x, data)
#        else:
#            plt.plot(data)

    if len(data.shape) == 1:
        if samp_rate > 1:
            x = np.arange((f0 - samp_rate/2)/1e6,(f0 + samp_rate/2)/1e6, samp_rate/len(data)/1e6)
            #x *= 1e3
            x = x[:len(data)]
            plt.plot(x, data, color=color)

            xlabel="Frequency in MHz"
            ylabel="DPA"
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
        else:
            plt.plot(data)

    # 2D Plots (stft)
    elif len(data.shape) == 2:
        xlabel="Frequency in MHz"
        ylabel="Time in ms"
        #if f0 > 0:
        extent = [  (f0 - samp_rate/2)/1e6,
                    (f0 + samp_rate/2)/1e6,
                    1e3 * len(data) * float(fft_step) / samp_rate,
                    0]
        print extent
        im = plt.imshow(data,interpolation='bilinear', extent=extent, aspect='auto')
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.colorbar(im)

    # dump
    if png != "":
        plt.savefig(png,dpi=50)

    if npy != "":
        np.save(npy, data)

    #arch show thread hack
    if blocking:
        plt.show()
        raw_input("press return to continue")
    else:
        p = Process(target=plt.show,args=(True,))
        p.start()

## graphing data
#def plot(   data,
#            samp_rate=1,
#            fft_step=1,
#            f0=0,
#            blocking=True,
#            clear=True,
#            png="/tmp/plot.png",
#            npy="/tmp/plot",
#            title="",
#            xlabel="Time in ms",
#            ylabel="Frequency in MHz"):
#    #global p
#    #if p is not None:
#    #    p.terminate()
#    #    p.join()
#
#    args = {    "data" : data,
#                "samp_rate" : samp_rate,
#                "fft_step" : fft_step,
#                "f0" : f0,
#                "blocking" : blocking,
#                "clear" : clear,
#                "png" : png,
#                "npy" : npy,
#                "title" : title,
#                "xlabel" : xlabel,
#                "ylabel" : ylabel}
#
#    p = Process(target=plot_thread, kwargs=args)
#    p.start()
#
#    if blocking:
#        raw_input("press return to continue")



p = None
plt.ion()
