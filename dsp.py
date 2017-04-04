import numpy as np
import matplotlib
import pylab as plt
from multiprocessing import Process
import threading
import time

# Fourier & Co.
def stft(trace, fft_len=1024, fft_step=2048, n_fft=0, log=True):
    if n_fft == 0:
        n_fft = int(np.ceil( (len(trace) - fft_len) / fft_step + 1))

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

from multiprocessing import Process,Queue

# graphing data
def plot(   data,
            samp_rate=1,
            fft_step=1,
            f0=0,
            blocking=True,
            clear=True,
            show=True,
            png="/tmp/plot.png",
            npy="/tmp/plot",
            title="",
            xlabel="Frequency in MHz",
            ylabel="Time in ms",
            color='k'):

        global plot_queue
        plot_queue.put((data,samp_rate,fft_step,f0,clear,show,png,npy,title,xlabel,ylabel,color))

        if blocking:
            raw_input("press return to continue")

def plot_process():
    while True:
        global plot_queue

        data,samp_rate,fft_step,f0,clear,show,png,npy,title,xlabel,ylabel,color  = plot_queue.get()

        if clear:
            plt.clf()

        if data is None:
            return

        matplotlib.rcParams.update({'font.size': 18})

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        #1D Graphs
        if len(data.shape) == 1:
            if samp_rate > 1:
                if f0 > 0:
                    x = np.arange((f0 - samp_rate/2)/1e6,(f0 + samp_rate/2)/1e6, samp_rate/len(data)/1e6)
                elif samp_rate > 1:
                    x = np.arange(0,len(data)) * 1e3 / samp_rate
                else:
                    x = np.arange(0,len(data))
                x = x[:len(data)]
                plt.plot(x, data, color=color)

                plt.xlabel(xlabel)
                plt.ylabel(ylabel)
            else:
                plt.plot(data)

        # 2D Plots (stft)
        elif len(data.shape) == 2:
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)

            if f0 > 0:
                extent = [  (f0 - samp_rate/2)/1e6,
                            (f0 + samp_rate/2)/1e6,
                            1e3 * len(data) * float(fft_step) / samp_rate,
                            0]
                im = plt.imshow(data,interpolation='bilinear', extent=extent, aspect='auto')
            else:
                im = plt.imshow(data,interpolation='bilinear', aspect='auto')
            plt.colorbar(im)

        # dump
        if png != "":
            plt.savefig(png,dpi=100)

        if npy != "":
            np.save(npy, data)

        if show:
            #plt.show()
            #block_queue.put("")
            #raw_input("press return to continue")
            plt.ion()
            plt.draw()
            plt.pause(.1)

plot_queue = Queue()
p = Process(target=plot_process)
p.deamon = True
p.start()
