#!/usr/bin/env python

import sys
import capture
import dsp
import os
import glob

#    def fine(self, trace, trigger, debug=False):
#        trigger_bin = self.trigger_bin
#        pre_trigger = self.pre_trigger
#        post_trigger = self.post_trigger
#        fft_step = self.fft_step #local rename
#
#        #store reference
#        if self.reference is None:
#            start = trigger-(pre_trigger*fft_step)
#            stop  = trigger+(post_trigger*fft_step)
#            self.reference = trace[start:stop]
#            return trigger
#
#        s = stft(trace[trigger-4096:trigger+4096], fft_len=self.fft_len, fft_step = 4)
#        trig = np.zeros(len(s))
#        for i in xrange(len(s)):
#            trig[i] = s[i,trigger_bin]
#
#        plot(trig)
#
#        return trigger

if __name__ == "__main__":
    cap = capture.capture(online=False)

    #postprocess
    for cfile in glob.glob("no-track/vmbox04-mul-8M/*.cfile"):
        print "processing %s" % cfile
        try:
            trace = dsp.load(cfile)
            trace = cap.align(trace, debug=False)
            dsp.save(trace, cfile)
        except Exception as e:
            print e
            os.remove(cfile)
