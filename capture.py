#!/usr/bin/env python

from random import shuffle, choice, getrandbits
import socket
import glob
import imp
import sys
import os
from multiprocessing import Process, Queue
import threading
import time

from config import config_get, config_set, config_reload
from dsp import *

import logging as log
log.basicConfig(filename='/dev/stdout', filemode='w', level=log.DEBUG)

class capture:
    def __init__(self):
        self.i = 0
        self.tb = None
        self.config_reload()

        if self.offline:
            self.files = glob.glob(self.tracedir + "/*.cfile")
            shuffle(self.files)
        else:
            self.trig_fifo = "/tmp/trig.fifo"
            self.demod_fifo = "/tmp/demod.fifo"

            log.debug( "creating fifo")
            self.bufflen = 16000
            try:
                os.unlink(self.trig_fifo)
                os.unlink(self.demod_fifo)
            except:
                pass

            os.mkfifo(self.trig_fifo)
            os.mkfifo(self.demod_fifo)

            self.recv_p = None
            self.tb = None
            self.restart_tb()

            dut = imp.load_source("dut",  config_get("dut"))
            self.dut = dut.dut()

        if self.dump:
            try:
                os.makedirs(self.tracedir)
            except:
                pass

    #load config from file
    def config_reload(self):
        config_reload()
        #config
        self.capture_frequency = config_get("capture.frequency", int)
        self.capture_samp_rate = config_get("capture.samp_rate", int)
        self.capture_gain = config_get("capture.gain", int)
        
        self.offline = False
        self.dump = False

        #trigger
        self.trigger_low_pass = config_get("trigger.low_pass", int)
        self.trigger_frequency = config_get("trigger.frequency", int)

        #demod
        self.demod_select = config_get("demod.select", list)
        self.demod_frequency = config_get("demod.frequency", int)
        self.demod_bandpass_low = config_get("demod.bandpass_low", int)
        self.demod_bandpass_high = config_get("demod.bandpass_high", int)
        self.demod_decimation = config_get("demod.decimation", int)

        #stft
        self.stft = config_get("preprocess.stft", bool)
        self.stft_log = config_get("preprocess.stft_log", bool)
        self.fft_len =  config_get("preprocess.fft_len", int)
        self.fft_step =  config_get("preprocess.fft_step", int)

        if self.demod_select[0] == 0:
            self.demod_decimation = 1
            self.frequency = self.capture_frequency
        elif self.demod_select[0] == 1:
            self.demod_decimation = 1
            self.frequency = self.trigger_frequency
        elif self.demod_select[0] == 2:
            self.frequency = self.trigger_frequency
        elif self.demod_select[0] == 3:
            self.frequency = 0

        self.samp_rate = self.capture_samp_rate / self.demod_decimation
        self.demod_bandpass_high = min(self.samp_rate / 2,  self.demod_bandpass_high)


    #configure the top_block
    def restart_tb(self):
        if self.tb is not None:
            log.debug("stop top_block")
            self.tb.stop()
            self.tb.wait()
            del self.tb

        if self.recv_p is not None:
            log.debug("stop recv_thread")
            self.recv_p.terminate()

        self.config_reload()

        #start recv_thread
        self.queue = Queue(maxsize=1024)
        self.recv_p = Process(target=self.read, args=(self.queue,))
        self.recv_p.start()

        #create top_block
        top_block = imp.load_source("top_block", "grc/cap-demod/top_block.py")
        tb = self.tb = top_block.top_block()
        log.debug("top_lock created")

        #top_block config
        tb.set_center_frequency(self.capture_frequency)
        tb.set_samp_rate(self.capture_samp_rate)
        tb.set_gain(self.capture_gain)
        tb.set_trigger_frequency(self.trigger_frequency)
        tb.set_trigger_low_pass(self.trigger_low_pass)

        tb.set_selector_1_input(self.demod_select[0])
        tb.set_selector_2_input(self.demod_select[1])
        tb.set_selector_3_input(self.demod_select[2])

        tb.set_demod_frequency(self.demod_frequency)
        tb.set_demod_decimation(self.demod_decimation)
        tb.set_demod_bandpass_high(self.demod_bandpass_high)
        tb.set_demod_bandpass_low(self.demod_bandpass_low)

        #start top_block
        self.tb.start()
        log.debug( "top block running")
        time.sleep(1) #wait for filters to initialize

    def configure_timig(self):
        t = time.time()
        self.dut.challenge(self.dut.values[0])
        self.trigger_execution_time = time.time() - t
        log.debug("dut execution time: %.2fms" % (self.trigger_execution_time * 1e3))
        config_set("trigger.execution_time", self.trigger_execution_time, float)
        self.trigger_delay = 5 * self.trigger_execution_time
        config_set("trigger.delay", self.trigger_delay, float)
        log.debug("using delay: %.2fms" % (self.trigger_delay * 1e3))


    def read(self, queue):
        log.debug("capture thread started")

        demod = open( self.demod_fifo, "rb")
        trig = open( self.trig_fifo, "rb")
        log.debug( "fifo open")

        while True:
            d = demod.read( 8*self.bufflen / self.demod_decimation)
            t = trig.read( 4*self.bufflen / 100)

            if queue.full():
                queue.get()
            queue.put( (t,d))

    def capture(self, values=None, debug=False, count=10):
        # TODO Offline Traces (currently disabled)
        if self.offline:
            cfile = self.files.pop()
            trace = load(cfile)
            challenge = os.path.basename(cfile).split("-")[1]
            challenge = challenge[0:-len(".cfile")]
            if debug:
                print "callenge: %s" % challenge
            return challenge,trace

        else:
            challenges, trig, demod = self.receive(values, debug, count)
            traces = self.extract(trig, demod, count, debug)

            if len(traces) != count:
                log.warn("extract failed")
                return []

            return zip(challenges, traces)

    def receive(self, values=None, debug=False, count=10):
        #performing count executions
        log.debug( "challenge")
        #flush data from recv. queue
        while self.queue.qsize() > 0: self.queue.get()

        #trigger count challenge executions
        challenges = []
        time.sleep(self.trigger_delay)
        for i in xrange(count):
            start = time.time()

            #perform one execution
            challenge = choice(self.dut.values) if values is None else choice(values)
            challenge = self.dut.values[i%len(self.dut.values)] if values is None else values[i%len(values)]
            if debug:
                print "callenge: %s" % challenge

            challenges += [challenge]
            self.dut.challenge(challenge)
            time.sleep(self.trigger_delay - (time.time() - start))

        time.sleep(self.trigger_delay)
        log.debug( "response")

        #get samples from queue
        t = (2+count) * self.trigger_delay #timespan of interest
        trig = ""
        demod = ""
        for i in xrange(int(self.capture_samp_rate * t / self.bufflen)):
            t,d = self.queue.get() 
            trig += t
            demod += d

        log.debug("converting %d and %d bytes" % (len(trig), len(demod)))
        trig = np.frombuffer(trig, dtype=np.dtype('f4'))
        demod = np.frombuffer(demod, dtype=np.dtype('c8'))
        if debug:
            log.debug("drawing plot")
            plot(stft(demod, self.fft_len, self.fft_step),
                    f0=self.frequency,
                    samp_rate=self.samp_rate,
                    fft_step=self.fft_step,
                    title="Raw Trace",
                    clear=True,
                    blocking=True)

        return challenges, trig, demod

    def find_trigger_frequency(self, demod, count=10):
        s = stft(demod, self.fft_len, self.fft_step)
        s = (s-s.mean(axis=0)) / s.std(axis=0)
        s = np.cumsum(s, axis=0)

        width = int(self.trigger_execution_time * self.capture_samp_rate / self.fft_step) / 2

        #use wavelets to search for count consecutive pulses
        pulses = np.zeros((self.trigger_delay * self.samp_rate / self.fft_step, self.fft_len))
        for offset in xrange(int(self.trigger_delay * self.samp_rate / self.fft_step)):
            p = np.zeros(self.fft_len)
            for i in xrange(10):
                o = int(offset + (self.trigger_delay * i * self.capture_samp_rate / self.fft_step))
                p += (s[o+width] - s[o]) + (s[o+3*width] - s[o+width]) - (s[o+4*width] - s[o+3*width])

            pulses[offset] = np.abs(p)


        b = np.unravel_index(pulses.argmax(), pulses.shape)[1]
        trigger_frequency = stft_bin2f(b, self.capture_frequency, self.fft_len, self.samp_rate)
        self.trigger_frequency = trigger_frequency
        config_set("trigger.frequency", trigger_frequency, float)
        log.debug("using trigger frequency %.3fMHz" % (trigger_frequency/1e6))

        plot(pulses,
            title="Pulse search",
            xlabel="Frequency in MHz",
            ylabel="Offset in ms",
            f0=self.frequency,
            samp_rate=self.samp_rate,
            fft_step=self.fft_step,
        )

        return trigger_frequency


    #haar wavelet transform
    def haar_transform(self, trig, width):
        ret = np.zeros(len(trig))
        s = np.cumsum(trig-trig.mean())
        for i in xrange(0,len(s) - 2*width):
            r = -(s[i+width] - s[i]) + (s[i+2*width] - s[i+width])
            ret[(i)] = np.abs(r/width)
        return ret

    #use trigger signal to extract executions from trace
    def extract( self, trig, demod, count, debug=False):
        trig_decimation = 100
        samp_rate = self.samp_rate

        if debug:
            plot(trig, samp_rate=self.samp_rate*self.demod_decimation/trig_decimation, ylabel="",title="Trigger Signal")

        #compute wavelet width by execution time
        width = int(self.trigger_execution_time * self.capture_samp_rate / trig_decimation) / 2
            
        #slope search by haar transform
        haar = self.haar_transform(trig, width)
        if debug:
            plot(haar,
                    samp_rate=self.samp_rate*self.demod_decimation/trig_decimation,
                    title="Haar transform",
                    xlabel="Time in ms",
                    ylabel="Wavelet Response")

        #extract slopes
        trigger = []
        for i in xrange(count*2):
            t = np.unravel_index(haar.argmax(), haar.shape)[0]
            haar[t-width:t+width] = 0
            trigger += [t+width]
        trigger = sorted(trigger)

        #extract traces
        traces = []
        for i in xrange(count):
            t = trigger[2*i]
            start = int((t*trig_decimation/self.demod_decimation) - (self.trigger_execution_time*0.2*samp_rate))
            stop  = int((t*trig_decimation/self.demod_decimation) + (self.trigger_execution_time*samp_rate))
            traces += [demod[start:stop]]
            
        return traces[::-1]

    def mask(self, stft):
        f1 = config_get("preprocess.mask_f1", float)
        f2 = config_get("preprocess.mask_f2", float)
        t1 = config_get("preprocess.mask_t1", float)
        t2 = config_get("preprocess.mask_t2", float)

        s = stft.shape
        mask = np.ones(s)

        for i in xrange(s[0]):
            if  i < float(t1)*s[0] or s[0]-i < float(t2)*s[0]:
                mask[i] = 0

        for i in xrange(s[1]):
            if np.abs(i - (s[1] / 2)) < float(f1)*s[1]:
                mask[:,i] = 0
            if  i < float(f2)*s[1] or s[1]-i < float(f2)*s[1]:
                mask[:,i] = 0

        return mask*stft


    def preprocess(self, trace, debug=False):
        s = trace

        if self.stft:
            s =  stft(s, self.fft_len, self.fft_step, log=self.stft_log)

            if debug:
                plot(s, f0=cap.frequency, samp_rate=cap.samp_rate, fft_step=pre.fft_step, title="Aligned Trace")
            if config_get("preprocess.mask", bool):
                s = self.mask(s)

        else:
            s = np.abs(s)


        return s

if __name__ == "__main__":
    cap = capture()

    cap.configure_timig()

    challenges, trig, demod = cap.receive(debug=True)
    cap.find_trigger_frequency(demod)
    cap.restart_tb()

    res = cap.capture(debug=True)
    try:
        for c, trace in res:
            plot(stft(trace,cap.fft_len,cap.fft_step),
                    f0=cap.frequency,
                    samp_rate=cap.samp_rate,
                    fft_step=cap.fft_step,
                    title="Aligned Trace",
                    clear=True,
                    blocking=True)
    except:
        pass

    os.kill(os.getpid(), 9)
