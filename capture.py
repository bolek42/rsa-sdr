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
import select
from Queue import PriorityQueue

from config import config_get, config_set, config_reload
from dsp import *

import logging as log
log.basicConfig(filename='/dev/stdout', filemode='w', level=log.DEBUG)

class capture:
    def __init__(self):
        self.i = 0
        self.tb = None
        self.reference = None
        self.do_read = False
        self.config_reload()
        self.demod_decimation = 1
        self.trig_decimation = 100

        if self.offline:
            self.files = glob.glob(self.tracedir + "/*.cfile")
            shuffle(self.files)
        else:
            self.trig_fifo = "/tmp/trig.fifo"
            self.demod_fifo = "/tmp/demod.fifo"

            log.debug( "creating fifo")
            self.bufflen = 1024
            try:
                os.unlink(self.trig_fifo)
                os.unlink(self.demod_fifo)
            except:
                pass

            os.mkfifo(self.trig_fifo)
            os.mkfifo(self.demod_fifo)

            #start recv_thread
            self.queue = Queue(maxsize=1024)
            self.recv_t = threading.Thread(target=self.read, args=(self.queue,))
            self.recv_t.start()

            #create top_block
            top_block = imp.load_source("top_block", "grc/top_block.py")
            self.tb = top_block.top_block()
            self.tb.Start(True)
            print "started"
            self.tb_t = threading.Thread(target=self.tb.Wait)
            self.tb_t.start()
            log.debug("top_block created")

            self.tb_configure()
            log.debug("top_bilock configured")

            dut = imp.load_source("dut",  config_get("dut"))
            self.dut = dut.dut()

        if self.dump:
            try:
                os.makedirs(self.tracedir)
            except:
                pass

    def set_center_frequency(self, f):
        self.center_frequency = config_set("capture.frequency", f, int)
        self.tb.set_center_frequency(f)
        self.restart_tb()

    def set_demod_frequency(self, f):
        self.center_frequency = config_set("capture.frequency", f, int)
        self.tb.set_center_frequency(f)
        self.restart_tb()

    #load config from file
    def config_reload(self):
        config_reload()
        #config
        self.center_frequency = config_get("capture.center_frequency", int)
        self.capture_samp_rate = config_get("capture.samp_rate", int)
        self.capture_gain = config_get("capture.gain", int)
        
        self.offline = False
        self.dump = False

        #trigger
        self.trigger_frequency = config_get("capture.trigger_frequency", int)
        self.trigger_delay = config_get("capture.delay", float)
        self.trigger_execution_time = config_get("capture.execution_time", float)

        #demod
        self.demod_select = config_get("capture.demod", int)
        self.demod_frequency = config_get("capture.demod_frequency", int)
        self.demod_lowpass = config_get("capture.demod_lowpass", int)
        self.demod_bandpass_low = config_get("capture.demod_bandpass_low", int)
        self.demod_bandpass_high = config_get("capture.demod_bandpass_high", int)

        #stft
        self.stft = config_get("preprocess.stft", bool)
        self.stft_log = config_get("preprocess.stft_log", bool)
        self.fft_len = config_get("preprocess.fft_len", int)
        self.fft_step = config_get("preprocess.fft_step", int)

    #load config from file
    def config_save(self):
        config_reload()
        #config
        config_set("capture.center_frequency", self.center_frequency, int)
        config_set("capture.samp_rate", self.capture_samp_rate, int)
        config_set("capture.gain", self.capture_gain, int)
        
        self.offline = False
        self.dump = False

        #trigger
        config_set("capture.trigger_frequency", self.trigger_frequency, int)
        config_set("capture.delay", self.trigger_delay, float)
        config_set("capture.execution_time", self.trigger_execution_time, float)

        #demod
        config_set("capture.demod", self.demod_select, int)
        config_set("capture.demod_frequency", self.demod_frequency, int)
        config_set("capture.demod_samp_rate", self.demod_samp_rate, int)
        config_set("capture.demod_lowpass", self.demod_lowpass, int)
        config_set("capture.demod_bandpass_low", self.demod_bandpass_low, int)
        config_set("capture.demod_bandpass_high", self.demod_bandpass_high, int)

        #stft
        config_set("preprocess.stft", self.stft, bool)
        config_set("preprocess.stft_log", self.stft_log, bool)
        config_set("preprocess.fft_len", self.fft_len, int)
        config_set("preprocess.fft_step", self.fft_step, int)


    def tb_configure(self):
        #top_block config
        self.tb.set_center_frequency(self.center_frequency)
        self.tb.set_samp_rate(self.capture_samp_rate)
        self.tb.set_gain(self.capture_gain)
        self.tb.set_trigger_frequency(self.trigger_frequency)

        self.tb.set_demod_select(self.demod_select)

        self.tb.set_demod_frequency(self.demod_frequency)
        self.tb.set_demod_lowpass(self.demod_lowpass)
        self.tb.set_demod_bandpass_high(self.demod_bandpass_high)
        self.tb.set_demod_bandpass_low(self.demod_bandpass_low)

        self.demod_decimation = self.tb.get_demod_decimation()
        self.demod_samp_rate = self.tb.get_demod_samp_rate()

        #start top_block
        time.sleep(1) #wait for filters to initialize

    def tb_get(self):
        #top_block config
        self.center_frequency = self.tb.get_center_frequency()
        self.capture_samp_rate = self.tb.get_samp_rate()
        self.capture_gain = self.tb.get_gain()
        self.trigger_frequency = self.tb.get_trigger_frequency()

        self.demod_select = self.tb.get_demod_select()

        self.demod_frequency = self.tb.get_demod_frequency()
        self.demod_lowpass = self.tb.get_demod_lowpass()
        self.demod_bandpass_high = self.tb.get_demod_bandpass_high()
        self.demod_bandpass_low = self.tb.get_demod_bandpass_low()

        self.demod_decimation = self.tb.get_demod_decimation()
        self.demod_samp_rate = self.tb.get_demod_samp_rate()

    def configure_timig(self):
        t = time.time()
        self.dut.challenge(self.dut.test_value)
        self.trigger_execution_time = time.time() - t
        log.debug("dut execution time: %.2fms" % (self.trigger_execution_time * 1e3))
        config_set("capture.execution_time", self.trigger_execution_time, float)
        self.trigger_delay = 5 * self.trigger_execution_time
        config_set("capture.delay", self.trigger_delay, float)
        log.debug("using delay: %.2fms" % (self.trigger_delay * 1e3))


    def read(self, queue):
        log.debug("capture thread started")

        demod = os.open( self.demod_fifo, os.O_RDONLY)
        trig = os.open( self.trig_fifo, os.O_RDONLY)
        log.debug( "fifo open")

        t = d = ""
        while True:
            time.sleep(0.001)

            bufflen = 1024 * self.demod_decimation * self.trig_decimation
            d_len = int(8*bufflen / self.demod_decimation)
            t_len = int(4*bufflen / self.trig_decimation)
            self.bufflen = bufflen

            #flush data
            while True:
                empty = True
                readable,_,_ = select.select([demod,trig], [], [], 0)
                if readable:
                    d = os.read(demod, d_len)
                    t = os.read(trig, t_len)
                    empty = False

                if empty:
                    break

            #read
            d = t = ""
            while self.do_read:
                time.sleep(0.001)
                readable,_,_ = select.select([demod, trig], [], [], 0)
                if readable:
                    d += os.read(demod, d_len)
                    t += os.read(trig, t_len)

                if queue.full():
                    queue.get()

                if len(d) > d_len and len(t) > t_len:
                    queue.put( (t[:t_len],d[:d_len]))
                    t = t[t_len:]
                    d = d[d_len:]

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
        self.do_read = True

        #trigger count challenge executions
        challenges = []
        time.sleep(self.trigger_delay)
        for i in xrange(count):
            start = time.time()

            #perform one execution
            challenge = self.dut.test_value if values is None else values[i%len(values)]
            if debug:
                print "callenge: %s" % challenge

            challenges += [challenge]
            self.dut.challenge(challenge)
            time.sleep(self.trigger_delay - (time.time() - start))

        time.sleep(self.trigger_delay)
        log.debug( "response")

        #get samples from queue
        t = (3+count) * self.trigger_delay #timespan of interest
        trig = ""
        demod = ""
        for i in xrange(int(self.capture_samp_rate * t / self.bufflen)):
            t,d = self.queue.get() 
            trig += t
            demod += d
        self.do_read = False

        log.debug("converting %d and %d bytes" % (len(trig), len(demod)))
        trig = np.frombuffer(trig, dtype=np.dtype('f4'))
        demod = np.frombuffer(demod, dtype=np.dtype('c8'))
        if debug:
            log.debug("drawing plot")
            plot(stft(demod, self.fft_len, self.fft_step),
                    f0=self.demod_frequency,
                    samp_rate=self.demod_samp_rate,
                    fft_step=self.fft_step,
                    title="Raw Trace",
                    png="/tmp/raw.png",
                    clear=True,
                    blocking=True)

        return challenges, trig, demod

    def pulse_search(self, demod, count=10, log=True):
        s = stft(demod, self.fft_len, self.fft_step, log=log)
        s = (s-s.mean(axis=0))# / s.std(axis=0)
        s = np.cumsum(s, axis=0)

        width = int(self.trigger_execution_time * self.demod_samp_rate / self.fft_step) / 2

        #use wavelets to search for count consecutive pulses
        pulses = np.zeros((int(self.trigger_delay * self.demod_samp_rate / self.fft_step), self.fft_len))
        for offset in xrange(int(self.trigger_delay * self.demod_samp_rate / self.fft_step)):
            p = np.zeros(self.fft_len)
            for i in xrange(10):
                o = int(offset + (self.trigger_delay * i * self.demod_samp_rate / self.fft_step))
                p += (s[o+width] - s[o]) + (s[o+3*width] - s[o+width]) - (s[o+4*width] - s[o+3*width])

            pulses[offset] = np.abs(p)

        return pulses


    def find_trigger_frequency(self, demod, count=10):
        pulses = self.pulse_search(demod, count)

        b = np.unravel_index(pulses.argmax(), pulses.shape)[1]
        trigger_frequency = stft_bin2f(b, self.demod_frequency, self.fft_len, self.demod_samp_rate)
        self.trigger_frequency = trigger_frequency
        config_set("capture.trigger_frequency", trigger_frequency, float)
        self.tb.set_trigger_frequency(self.trigger_frequency)
        log.debug("using trigger frequency %.3fMHz" % (trigger_frequency/1e6))

        plot(pulses,
            title="Multi Pulse Response",
            xlabel="Frequency in MHz",
            ylabel="Offset in ms",
            f0=self.demod_frequency,
            samp_rate=self.demod_samp_rate,
            fft_step=self.fft_step,
            png="/tmp/multi_pulse.png"
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
        trig_decimation = self.trig_decimation

        if debug:
            plot(trig,
                samp_rate=self.capture_samp_rate*self.demod_decimation/trig_decimation, 
                ylabel="",
                xlabel="Time in ms",
                title="Trigger Signal",
                png="/tmp/trig.png")
                

        #compute wavelet width by execution time
        width = int(self.trigger_execution_time * self.demod_samp_rate / trig_decimation) / 2
            
        #slope search by haar transform
        haar = self.haar_transform(trig, width)
        if debug:
            plot(haar,
                    samp_rate=self.capture_samp_rate*self.demod_decimation/trig_decimation,
                    title="Haar Transform",
                    xlabel="Time in ms",
                    ylabel="Wavelet Response",
                    png="/tmp/haar.png")

        #extract slopes
        trigger = []
        for i in xrange(count*2):
            t = np.unravel_index(haar.argmax(), haar.shape)[0]
            haar[t-width:t+width] = 0
            trigger += [t+width]
        trigger = sorted(trigger)

        #upate execution time
        if debug:
            self.trigger_execution_time = 0
            for i in xrange(count):
                t = float(trigger[2*i+1] - trigger[2*i]) * trig_decimation / self.capture_samp_rate
                self.trigger_execution_time += t
            self.trigger_execution_time /= count
            log.debug("dut execution time: %.2fms" % (self.trigger_execution_time * 1e3))
            config_set("capture.execution_time", self.trigger_execution_time, float)

        #extract traces
        traces = []
        for i in xrange(count):
            t = trigger[2*i]
            start = int((t*trig_decimation/self.demod_decimation) - (self.trigger_execution_time*0.3*self.demod_samp_rate))
            stop  = int((t*trig_decimation/self.demod_decimation) + (self.trigger_execution_time*1.2*self.demod_samp_rate))
            trace = demod[start:stop]
            traces += [trace]

        return traces

    def static_alignment_stft(self, s, debug=False):
        if self.reference is None:
            self.reference = s
            np.save("/tmp/reference", s)
            return s

        #compute distance_matrix
        cost = np.corrcoef(s, self.reference)
        cost = 1-cost[:len(s),len(s):]
        cost -= np.min(cost)

        queue = PriorityQueue()
        queue.put((0,(0,0)))

        #compute offset
        dist = []
        offset_min, dist_min = 0,np.inf
        for offset in xrange(-len(s)/4, len(s)/4):
            d = 0
            i = j = 0

            #start
            if offset > 0:
                for i in xrange(offset):
                    d += cost[i,j]
            if offset < 0:
                for j in xrange(-offset):
                    d += cost[i,j]

            #diagonal walk
            while i < len(s)-1 and j < len(s)-1:
                d += cost[i,j]
                i,j = min(i+1,len(s)-1), min(j+1,len(s)-1)

            #end
            while i < len(s) - 1:
                d += cost[i,j]
                i = min(i+1,len(s)-1)

            while j < len(s) - 1:
                d += cost[i,j]
                j = min(j+1,len(s)-1)

            dist += [d]
            if d < dist_min:
                offset_min, dist_min = offset, d

        if debug:
            print "offset = %d" % offset_min
            plot(np.array(dist))

        #map
        ret = [[]] * len(s)
        i = j = 0
        #start
        if offset_min > 0:
            for i in xrange(offset_min):
                ret[j] = s[i]
        if offset_min < 0:
            for j in xrange(-offset_min):
                ret[j] = s[i]

        #diagonal walk
        while i < len(s)-1 and j < len(s)-1:
            ret[j] = s[i]
            i,j = min(i+1,len(s)-1), min(j+1,len(s)-1)

        #end
        while i < len(s) - 1:
            ret[j] = s[i]
            i = min(i+1,len(s)-1)

        while j < len(s) - 1:
            ret[j] = s[i]
            j = min(j+1,len(s)-1)
        ret[-1] = s[-1]

        return np.array(ret)

    def elastic_alignment_stft(self, s, debug=False):
        if self.reference is None:
            self.reference = s
            return s

        #compute distance_matrix
        cost = np.corrcoef(s, self.reference)
        cost = 1-cost[:len(s),len(s):]
        cost -= np.min(cost)

        queue = PriorityQueue()
        queue.put((0,(0,0)))

        #dijkstra
        dist = np.zeros(cost.shape) + np.inf
        path = {}
        while True:
            d, p = queue.get()
            i,j = p

            if i == j == len(s) - 1:
                break

            if abs(i-j) > len(s)*0.2:
                continue

            for x,y in [(1,0),(0,1),(1,1)]:
                if x+i >= len(s) or y+j >= len(s):
                    continue

                if d + cost[i+x,j+y] < dist[i+x,j+y]:
                    path[(i+x,j+y)] = (i,j)
                    dist[i+x,j+y] = d + cost[i+x,j+y]
                    queue.put((d + cost[i+x,j+y], (i+x,j+y,)))

        if debug:
            i = j = len(s) - 1
            while i != 0 or j != 0:
                cost[i,j] = -1
                i,j = path[(i,j)]
                
            cost[0,0] = -1
            plot(cost)

        #map
        ret = [[]] * len(s)
        i = j = len(s) - 1
        while True:
            ret[j] = s[i]
            if i == 0 and j == 0:
                break
            i,j = path[(i,j)]

        return np.array(ret)
            


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
            s = stft(s, self.fft_len, self.fft_step, log=self.stft_log)
            if config_get("preprocess.static_alignmet", bool):
                s = self.static_alignment_stft(s)

            if debug:
                plot(s,
                        f0=cap.frequency,
                        samp_rate=cap.samp_rate,
                        fft_step=pre.fft_step,
                        title="Aligned Trace",
                        png="/tmp/aligned.png")

            if config_get("preprocess.mask", bool):
                s = self.mask(s)

        return s

if __name__ == "__main__":
    import readline
    cap = capture()
    cap.configure_timig()

    cmd = ""
    while cmd not in ["q","quit"]:
        cmd = raw_input("capture> ")

        if cmd == "scan":
            try:
                f = int(raw_input("Start: "))
                stop = int(raw_input("Stop: "))
                f0 = f
                sr = 0
                ret = []
                cap.tb.set_demod_select(0)
                cap.tb.set_demod_decimation(1)
                cap.tb.set_demod_lowpass(cap.capture_samp_rate/2)
                while f < stop:
                    cap.tb.set_center_frequency(f)
                    challenges, trig, demod = cap.receive(debug=False, count=10)
                    pulses = cap.pulse_search(demod, 10, log=False)
                    ret += list(np.max(pulses, axis=0))

                    plot(   np.array(ret),
                            f0=f0,
                            samp_rate=sr,
                            fft_step=cap.fft_step,
                            title="Trigger Scan",
                            ylabel="Wavelet Response",
                            clear=True,
                            blocking=False,
                            png="/tmp/trigger_scan.png")

                    f += cap.capture_samp_rate
                    sr += cap.capture_samp_rate
                    f0 += cap.capture_samp_rate / 2
            except:
                import traceback; traceback.print_exc()
            

        if cmd == "trigger":
            challenges, trig, demod = cap.receive(debug=True)
            cap.find_trigger_frequency(demod)
            cap.reference = None

        if cmd == "challenge":
            for i in xrange(10):
                print "challenge"
                cap.dut.challenge(cap.dut.test_value)
                time.sleep(0.03)

        if cmd == "capture":
            cap.tb_get()
            res = cap.capture(debug=True)
            try:
                i = 0
                for c, trace in res:
                    s = stft(trace,cap.fft_len,cap.fft_step)
                    s = cap.static_alignment_stft(s, debug=True)
                    plot(   s,
                            f0=cap.demod_frequency,
                            samp_rate=cap.demod_samp_rate,
                            fft_step=cap.fft_step,
                            title="Aligned Trace %d" % i,
                            clear=True,
                            blocking=True,
                            png="/tmp/trace-%d" % i)
                    i+=1
            except:
                import traceback; traceback.print_exc()
                pass

        if cmd == "save":
            cap.tb_get()
            cap.config_save()

        if cmd == "help":
            print "trigger          configure trigger frequency"
            print "challenge        send challenge to dut"
            print "capture          capture traces"
            print "save             save configuration"
            print "quit             quit capture"

    print "Done"
    os.kill(os.getpid(), 9)
