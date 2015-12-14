import os
import Gnuplot, Gnuplot.funcutils
import traceback
import sys

from config import config_get, config_reload
from capture import *
from random import choice, randrange

class dpa:
    def __init__(self):
        self.reset()

        self.apply_config()
        self.cap = capture()

    def reset(self):
        self.sigma = {}
        self.n = {}
        self.error = {}


    def apply_config(self):
        self.outdir = config_get("misc.outdir", str)
        self.samp_rate = config_get("capture.samp_rate", int)

    def add(self, group, trace):
        #trace = np.sum(trace, axis=0)
        # inf -> NaN
        if np.isinf(trace).any():
            trace[np.isinf(trace)] = np.nan

        if group not in self.sigma:
            self.sigma[group] = np.zeros(trace.shape)
            self.n[group] = np.zeros(trace.shape)
            self.error[group] = []

        sigma = self.sigma[group]
        if sigma.shape == trace.shape:
            nan = np.isnan(trace)
            self.sigma[group][~nan] += trace[~nan]
            self.n[group] += ~nan
        else:
            print "dpa error: trace has invalid shape"

    # Bestimme den Mittelwert einer Grupper
    def mean(self, group, cache_error=10):
        if group not in self.sigma:
            return None

        m = self.sigma[group] / self.n[group]
        if self.outdir is not None:
            np.save("%s/mean-%s" % (self.outdir, group[:64]), m)

        return m

    # Bestimme die DPA differenz: E(A)-E(B)
    def dpa(self, A, B, verbose=True):
        if A not in self.sigma or B not in self.sigma:
            print "dpa error: invalid group"
            return np.array([])

        a = self.mean(A)
        b = self.mean(B)

        if a.shape != b.shape:
            print "dpa error: invalid shape"
            return np.array([])

        d = a - b
        if verbose:
            print "\x1b[0;0H"+"\x1b[2J",
            print "dpa groups: %d:%d" % (self.n[A].max(), self.n[B].max())
            print "dpa shape: " + str(d.shape)
            print "dpa max: %f" % np.max(d)
            print "dpa min: %f" % np.min(d)
        if self.outdir is not None:
            np.save("%s/dpa-%s-%s" % (self.outdir, A[:64],B[:64]), d)

        return d

    def oracle(self, runs=10000, values=None, verbose=True, reference=None, mask=None, max_trace=0, count=30):
            

        #perform dpa attack for values
        dp = None
        i = 0
        while i < runs:
            i += count
            # DPA #
            val = None
            try:
                #Capture traces
                res = []
                while len(res) == 0:
                    # Maximale Anzahl der Messungen pro gruppe
                    if values is not None:
                        val = filter( lambda v:   max_trace == 0 or
                                                v not in self.n or 
                                                max_trace > self.n[v].max(),
                                                values)
                        # finished, return
                        if len(val) == 0:
                            dp = self.dpa(a,b)
                            #self.reset()
                            return np.min(dp), np.max(dp)
                            return dp
                    res = self.cap.capture(values=val, count=count)
                
                ##gui
                #if dp is None or len(dp) == 0:
                #    dp = [0]
                #print "\rrun %d \t%f-(%f)=%f\tchallenge: %s" % (i, np.max(dp), np.min(dp), np.max(dp) - np.min(dp), repr(challenge)[0:64] ),
                #sys.stdout.flush()

                for challenge, t in res:
                    s = self.cap.preprocess(t)
                    #s = np.sum(s,axis=0)
                    self.add(challenge, s)
                    sys.stderr.write(".")

            except IndexError:
                print traceback.format_exc()
                break
            except Exception as e:
                print traceback.format_exc()

            # Zeige das aktuelle DPA
            if i % 1 == 0:
                try:
                    if values is None:
                        a = self.n.keys()[0]
                        b = self.n.keys()[1]
                    else:
                        a = values[0]
                        b = values[1]
                    
                    dp = self.dpa(a,b,verbose=verbose)

                    title = "Run %d" % (i)
                    plot(   dp,
                            f0=self.cap.frequency,
                            samp_rate=self.cap.samp_rate,
                            fft_step=self.cap.fft_step,
                            blocking=False,
                            ylabel="Frequency",
                            png="%s/%d.png" % (self.outdir,i), title=title)
                except Exception as e:
                    print traceback.format_exc()

        a = values[0]
        b = values[1]
        dp = self.dpa(a,b)

        self.reset()
        return np.min(dp), np.max(dp)
        return dp

    def get_refernece(self):
        while True:
            trace = None
            while trace is None:
                challenge,trace = self.cap.capture()
            detected_interupts, s = self.preprocess(trace)

            plot(s,blocking=False)
            if raw_input("Use as Reference?") in ["y","Y"]:
                return s
        

if __name__ == "__main__":
    dpa = dpa()
    mask = None
    #mask = dpa.mask(0.05, 0.02, 0.05, 0.05) #DC
    p,n = dpa.oracle(runs=10000, mask=mask)#,reference=dpa.get_refernece())
    print "min: %f\t max: %f" % (p,n)
    raw_input("press return to exit")
