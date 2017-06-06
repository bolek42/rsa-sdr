import readline
import sys
import numpy as np


from config import *
from capture import capture
from dpa import dpa
from dsp import *

if __name__ == "__main__":
    cap = capture()

    cmd = ""
    while cmd not in ["q","quit"]:
        cmd = raw_input("\033[0;33mrsa-sdr>\033[00m ")
        cmd = cmd.split(" ")

        if cmd[0] == "scan":
            try:
                f = int(cmd[1])
                stop = int(cmd[2])
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

        if cmd[0] == "scan-dpa":
            try:
                f = int(cmd[1])
                stop = int(cmd[2])
                a = cmd[3]
                b = cmd[4]
                f0 = f
                sr = 0
                ret = []
                cap.tb.set_demod_select(0)
                cap.tb.set_demod_decimation(1)
                cap.tb.set_demod_lowpass(cap.capture_samp_rate/2)
                d = dpa(cap=cap)
                while f < stop:
                    cap.tb.set_center_frequency(f)
                    challenges, trig, demod = cap.receive()
                    cap.find_trigger_frequency(demod)
                    cap.reference = None

                    for i in xrange(10):
                        res = d.cap.capture(values=[a,b], count=30)
                        for challenge, t in res:
                            s = d.cap.preprocess(t)
                            d.add(challenge, s)
                            sys.stderr.write(".")

                    dp = d.dpa(a,b)
                    ret += list(np.max(dp, axis=0))
                    d.reset()

                    plot(   np.array(ret),
                            f0=f0,
                            samp_rate=sr,
                            fft_step=cap.fft_step,
                            title="Scanning DPA",
                            clear=True,
                            blocking=False,
                            png="/tmp/trigger_scan.png")

                    f += cap.capture_samp_rate
                    sr += cap.capture_samp_rate
                    f0 += cap.capture_samp_rate / 2
            except:
                import traceback; traceback.print_exc()

        if cmd[0] == "dpa":
            n = int(cmd[1])
            a = cmd[2]
            b = cmd[3]
            try:
                dpa = dpa(cap=cap)
                p,n = dpa.oracle(values=[a,b], runs=n)
            except KeyboardInterrupt:
                pass

        if cmd[0] == "mean":
            n = int(cmd[1])
            a = cmd[2]
            d = dpa(cap=cap)
            cap.reference = None
            for i in xrange(n/10):
                res = d.cap.capture(values=[a], count=10)
                for challenge, t in res:
                    s = cap.preprocess(t)
                    d.add(challenge, s)
                    sys.stderr.write(".")

                plot(   d.mean(a),
                        f0=cap.demod_frequency,
                        samp_rate=cap.demod_samp_rate,
                        fft_step=cap.fft_step,
                        title="Mean",
                        clear=True,
                        blocking=False,
                        png="/tmp/mean.png")
                print ""

        if cmd[0] == "trigger":
            cap.configure_timig()
            challenges, trig, demod = cap.receive(debug=True)
            cap.find_trigger_frequency(demod, debug=True)
            cap.reference = None

        if cmd[0] == "config":
            if len(cmd) == 1:
                show_cfg()
            else:
                k = cmd[1]
                v = cmd[2]
                config_set(k,v)
                cap.config_reload()
                cap.tb_configure()

        if cmd[0] == "challenge":
            for i in xrange(10):
                print "challenge"
                cap.dut.challenge(cap.dut.test_value)
                time.sleep(0.03)

        if cmd[0] == "capture":
            cap.tb_get()
            res = cap.capture(debug=True)
            try:
                i = 0
                for c, trace in res[:1]:
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

        if cmd[0] == "save":
            if len(cmd) == 2:
                print "fooooooooooooo"
                cf = config_file
                set_config_file(cmd[1])
            cap.tb_get()
            cap.config_save()
            if len(cmd) == 2:
                set_config_file(cf)

        if cmd[0] == "help":
            print "scan start stop          scan fpr suitable trigger frequencies"
            print "trigger                  configure trigger frequency"
            print "capture                  capture traces"
            print "config                   show configuration"
            print "config key value         set configuration"
            print "challenge                send challenge to dut"
            print "mean count challenge     show mean for count traces"
            print "dpa count A B            perform dpa for args A and B"
            print "save                     save configuration"
            print "save config.json         save configuration"
            print "quit                     quit capture"

    print "Done"
    os.kill(os.getpid(), 9)
