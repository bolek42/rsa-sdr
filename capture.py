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

from config import config_get, config_reload
from dsp import *
from dut import *

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


            self.dut=dut()

        if self.dump:
            try:
                os.makedirs(self.tracedir)
            except:
                pass

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
        self.trigger_delay = config_get("trigger.delay", float)
        self.trigger_pre = config_get("trigger.pre", float)
        self.trigger_post = config_get("trigger.post", float)

        #demod
        self.demod_select = config_get("demod.select", list)
        self.demod_frequency = config_get("demod.frequency", int)
        self.demod_lowpass = config_get("demod.lowpass", int)
        self.demod_bandpass_low = config_get("demod.bandpass_low", int)
        self.demod_bandpass_high = config_get("demod.bandpass_high", int)
        self.demod_decimation = config_get("demod.decimation", int)

        #stft
        self.stft = config_get("preprocess.stft", bool)
        self.stft_log = config_get("preprocess.stft_log", bool)
        self.fft_len =  config_get("preprocess.fft_len", int)
        self.fft_step =  config_get("preprocess.fft_step", int)

        self.samp_rate = self.capture_samp_rate / self.demod_decimation
        self.demod_bandpass_high = min(self.samp_rate / 2,  self.demod_bandpass_high)

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

        

    def restart_tb(self):
        if self.tb is not None:
            log.debug( "stop top_block")
            self.tb.stop()
            self.tb.wait()
            del self.tb

        if self.recv_p is not None:
            log.debug( "stop recv_thread")
            self.recv_p.terminate()

        self.config_reload()

        #start recv_thread
        self.queue = Queue(maxsize=1024)
        self.recv_p = Process(target=self.receive, args=(self.queue,))
        self.recv_p.start()

        #create top_block
        log.debug( "creating top_block")
        top_block = imp.load_source( "top_block", "grc/cap-demod/top_block.py")
        log.debug( "creating top_block")
        tb = self.tb = top_block.top_block()
        log.debug( "top Block created")

        #top_block config
        tb.set_center_frequency(self.capture_frequency)
        tb.set_samp_rate(self.capture_samp_rate)
        tb.set_gain(self.capture_gain)
        tb.set_trigger_frequency(self.trigger_frequency)

        tb.set_selector_1_input(self.demod_select[0])
        tb.set_selector_2_input(self.demod_select[1])
        tb.set_selector_3_input(self.demod_select[2])

        tb.set_demod_frequency(self.demod_frequency)
        tb.set_demod_lowpass(self.demod_lowpass)
        tb.set_demod_decimation(self.demod_decimation)
        tb.set_demod_bandpass_high(self.demod_bandpass_high)
        tb.set_demod_bandpass_low(self.demod_bandpass_low)

        #start top_block
        self.tb.start()
        log.debug( "top block running")
        time.sleep(1) #wait for filters to initialize

            

    def receive( self, queue):
        log.debug( "capture thread started")

        demod = open( self.demod_fifo, "rb")
        trig = open( self.trig_fifo, "rb")
        log.debug( "fifo open")

        while True:
            d = demod.read( 8*self.bufflen / self.demod_decimation)
            t = trig.read( 4*self.bufflen / 100)

            if queue.full():
                queue.get()
            queue.put( (t,d))

    def capture(self, values=None, debug=False, count=10, delay=0.2):
        # Offline Traces XXX
        if self.offline:
            cfile = self.files.pop()
            trace = load(cfile)
            challenge = os.path.basename(cfile).split("-")[1]
            challenge = challenge[0:-len(".cfile")]
            if debug:
                print "callenge: %s" % challenge
            return challenge,trace

        # Messung mittels SDR
        else:

            #actually performing rsa computation
            log.debug( "challenge")
            #flush data from queu
            while self.queue.qsize() > 0: self.queue.get()

            #trigger count challenge executions
            challenges = []
            for i in xrange(count):
                start = time.time()

                challenge = choice(self.dut.values) if values is None else choice(values)
                challenge = self.dut.values[i%len(self.dut.values)] if values is None else values[i%len(values)]
                if debug:
                    print "callenge: %s" % challenge

                challenges += [challenge]
                self.dut.challenge( challenge)
                time.sleep(self.trigger_delay - (time.time() - start))

            log.debug( "response")

            #get data from queue
            t = count * self.trigger_delay + 0.3 #timespan of interest
            trig = ""
            demod = ""
            for i in xrange( int(self.capture_samp_rate * t / self.bufflen)):
                t,d = self.queue.get() 
                trig += t
                demod += d

        with open("/tmp/demod.cfile","wb") as f:
            f.write(demod)
        

        log.debug( "converting %d and %d bytes" % (len(trig), len(demod)))
        trig = np.frombuffer(trig, dtype=np.dtype('f4'))
        demod = np.frombuffer(demod, dtype=np.dtype('c8'))
        if debug:
            plot(stft( demod,cap.fft_len,cap.fft_step),
                    f0=cap.frequency,
                    samp_rate=cap.samp_rate,
                    fft_step=cap.fft_step,
                    title="Raw Trace",
                    clear=True,
                    blocking=True)

        log.debug( "extract")
        traces = self.extract( demod, trig, count, self.trigger_delay, debug=debug)
        if len(traces) != count:
            log.warn("extract failed")
            return []

        return zip(challenges, traces)

    def extract( self, demod, trig, count, delay, debug=False):
        threshold = trig.mean()
        trig_decimation = 100
        samp_rate = self.samp_rate
        pre_trigger = self.trigger_pre
        post_trigger = self.trigger_post

        if debug:
            plot(trig, samp_rate=20e3, ylabel="",title="Trigger Signal")

        traces = []
        stop2 = 0
        for i in xrange( len( trig)-1, 1, -1):
            if trig[i-1] > threshold and trig[i] <= threshold: 
                start = ((i*trig_decimation/self.demod_decimation) - (pre_trigger*samp_rate))
                stop  = ((i*trig_decimation/self.demod_decimation) + (post_trigger*samp_rate))

                #use delay to drop false trigger points
                d = (stop2 - stop)/samp_rate
                if stop2 != 0 and np.abs( d - delay) > 0.08 * delay:
                    print "skip %f" % (d * 1000)
                    continue

                stop2 = stop
                traces += [demod[start:stop]]

        print len(traces)
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

    while True:
        res = cap.capture(debug=True)
        try:
            for c, trace in [res[0]]:
                plot(stft( trace,cap.fft_len,cap.fft_step),
                        f0=cap.frequency,
                        samp_rate=cap.samp_rate,
                        fft_step=cap.fft_step,
                        title="Aligned Trace",
                        clear=True,
                        blocking=True)
        except:
            pass
        cap.restart_tb()
