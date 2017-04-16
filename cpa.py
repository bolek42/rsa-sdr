import struct
from binascii import hexlify, unhexlify


sboxes = [
   [0x01010400, 0x00000000, 0x00010000, 0x01010404,
    0x01010004, 0x00010404, 0x00000004, 0x00010000,
    0x00000400, 0x01010400, 0x01010404, 0x00000400,
    0x01000404, 0x01010004, 0x01000000, 0x00000004,
    0x00000404, 0x01000400, 0x01000400, 0x00010400,
    0x00010400, 0x01010000, 0x01010000, 0x01000404,
    0x00010004, 0x01000004, 0x01000004, 0x00010004,
    0x00000000, 0x00000404, 0x00010404, 0x01000000,
    0x00010000, 0x01010404, 0x00000004, 0x01010000,
    0x01010400, 0x01000000, 0x01000000, 0x00000400,
    0x01010004, 0x00010000, 0x00010400, 0x01000004,
    0x00000400, 0x00000004, 0x01000404, 0x00010404,
    0x01010404, 0x00010004, 0x01010000, 0x01000404,
    0x01000004, 0x00000404, 0x00010404, 0x01010400,
    0x00000404, 0x01000400, 0x01000400, 0x00000000,
    0x00010004, 0x00010400, 0x00000000, 0x01010004],

   [0x80108020, 0x80008000, 0x00008000, 0x00108020,
    0x00100000, 0x00000020, 0x80100020, 0x80008020,
    0x80000020, 0x80108020, 0x80108000, 0x80000000,
    0x80008000, 0x00100000, 0x00000020, 0x80100020,
    0x00108000, 0x00100020, 0x80008020, 0x00000000,
    0x80000000, 0x00008000, 0x00108020, 0x80100000,
    0x00100020, 0x80000020, 0x00000000, 0x00108000,
    0x00008020, 0x80108000, 0x80100000, 0x00008020,
    0x00000000, 0x00108020, 0x80100020, 0x00100000,
    0x80008020, 0x80100000, 0x80108000, 0x00008000,
    0x80100000, 0x80008000, 0x00000020, 0x80108020,
    0x00108020, 0x00000020, 0x00008000, 0x80000000,
    0x00008020, 0x80108000, 0x00100000, 0x80000020,
    0x00100020, 0x80008020, 0x80000020, 0x00100020,
    0x00108000, 0x00000000, 0x80008000, 0x00008020,
    0x80000000, 0x80100020, 0x80108020, 0x00108000],

   [0x00000208, 0x08020200, 0x00000000, 0x08020008,
    0x08000200, 0x00000000, 0x00020208, 0x08000200,
    0x00020008, 0x08000008, 0x08000008, 0x00020000,
    0x08020208, 0x00020008, 0x08020000, 0x00000208,
    0x08000000, 0x00000008, 0x08020200, 0x00000200,
    0x00020200, 0x08020000, 0x08020008, 0x00020208,
    0x08000208, 0x00020200, 0x00020000, 0x08000208,
    0x00000008, 0x08020208, 0x00000200, 0x08000000,
    0x08020200, 0x08000000, 0x00020008, 0x00000208,
    0x00020000, 0x08020200, 0x08000200, 0x00000000,
    0x00000200, 0x00020008, 0x08020208, 0x08000200,
    0x08000008, 0x00000200, 0x00000000, 0x08020008,
    0x08000208, 0x00020000, 0x08000000, 0x08020208,
    0x00000008, 0x00020208, 0x00020200, 0x08000008,
    0x08020000, 0x08000208, 0x00000208, 0x08020000,
    0x00020208, 0x00000008, 0x08020008, 0x00020200],

   [0x00802001, 0x00002081, 0x00002081, 0x00000080,
    0x00802080, 0x00800081, 0x00800001, 0x00002001,
    0x00000000, 0x00802000, 0x00802000, 0x00802081,
    0x00000081, 0x00000000, 0x00800080, 0x00800001,
    0x00000001, 0x00002000, 0x00800000, 0x00802001,
    0x00000080, 0x00800000, 0x00002001, 0x00002080,
    0x00800081, 0x00000001, 0x00002080, 0x00800080,
    0x00002000, 0x00802080, 0x00802081, 0x00000081,
    0x00800080, 0x00800001, 0x00802000, 0x00802081,
    0x00000081, 0x00000000, 0x00000000, 0x00802000,
    0x00002080, 0x00800080, 0x00800081, 0x00000001,
    0x00802001, 0x00002081, 0x00002081, 0x00000080,
    0x00802081, 0x00000081, 0x00000001, 0x00002000,
    0x00800001, 0x00002001, 0x00802080, 0x00800081,
    0x00002001, 0x00002080, 0x00800000, 0x00802001,
    0x00000080, 0x00800000, 0x00002000, 0x00802080],

   [0x00000100, 0x02080100, 0x02080000, 0x42000100,
    0x00080000, 0x00000100, 0x40000000, 0x02080000,
    0x40080100, 0x00080000, 0x02000100, 0x40080100,
    0x42000100, 0x42080000, 0x00080100, 0x40000000,
    0x02000000, 0x40080000, 0x40080000, 0x00000000,
    0x40000100, 0x42080100, 0x42080100, 0x02000100,
    0x42080000, 0x40000100, 0x00000000, 0x42000000,
    0x02080100, 0x02000000, 0x42000000, 0x00080100,
    0x00080000, 0x42000100, 0x00000100, 0x02000000,
    0x40000000, 0x02080000, 0x42000100, 0x40080100,
    0x02000100, 0x40000000, 0x42080000, 0x02080100,
    0x40080100, 0x00000100, 0x02000000, 0x42080000,
    0x42080100, 0x00080100, 0x42000000, 0x42080100,
    0x02080000, 0x00000000, 0x40080000, 0x42000000,
    0x00080100, 0x02000100, 0x40000100, 0x00080000,
    0x00000000, 0x40080000, 0x02080100, 0x40000100],

   [0x20000010, 0x20400000, 0x00004000, 0x20404010,
    0x20400000, 0x00000010, 0x20404010, 0x00400000,
    0x20004000, 0x00404010, 0x00400000, 0x20000010,
    0x00400010, 0x20004000, 0x20000000, 0x00004010,
    0x00000000, 0x00400010, 0x20004010, 0x00004000,
    0x00404000, 0x20004010, 0x00000010, 0x20400010,
    0x20400010, 0x00000000, 0x00404010, 0x20404000,
    0x00004010, 0x00404000, 0x20404000, 0x20000000,
    0x20004000, 0x00000010, 0x20400010, 0x00404000,
    0x20404010, 0x00400000, 0x00004010, 0x20000010,
    0x00400000, 0x20004000, 0x20000000, 0x00004010,
    0x20000010, 0x20404010, 0x00404000, 0x20400000,
    0x00404010, 0x20404000, 0x00000000, 0x20400010,
    0x00000010, 0x00004000, 0x20400000, 0x00404010,
    0x00004000, 0x00400010, 0x20004010, 0x00000000,
    0x20404000, 0x20000000, 0x00400010, 0x20004010],

   [0x00200000, 0x04200002, 0x04000802, 0x00000000,
    0x00000800, 0x04000802, 0x00200802, 0x04200800,
    0x04200802, 0x00200000, 0x00000000, 0x04000002,
    0x00000002, 0x04000000, 0x04200002, 0x00000802,
    0x04000800, 0x00200802, 0x00200002, 0x04000800,
    0x04000002, 0x04200000, 0x04200800, 0x00200002,
    0x04200000, 0x00000800, 0x00000802, 0x04200802,
    0x00200800, 0x00000002, 0x04000000, 0x00200800,
    0x04000000, 0x00200800, 0x00200000, 0x04000802,
    0x04000802, 0x04200002, 0x04200002, 0x00000002,
    0x00200002, 0x04000000, 0x04000800, 0x00200000,
    0x04200800, 0x00000802, 0x00200802, 0x04200800,
    0x00000802, 0x04000002, 0x04200802, 0x04200000,
    0x00200800, 0x00000000, 0x00000002, 0x04200802,
    0x00000000, 0x00200802, 0x04200000, 0x00000800,
    0x04000002, 0x04000800, 0x00000800, 0x00200002],

   [0x10001040, 0x00001000, 0x00040000, 0x10041040,
    0x10000000, 0x10001040, 0x00000040, 0x10000000,
    0x00040040, 0x10040000, 0x10041040, 0x00041000,
    0x10041000, 0x00041040, 0x00001000, 0x00000040,
    0x10040000, 0x10000040, 0x10001000, 0x00001040,
    0x00041000, 0x00040040, 0x10040040, 0x10041000,
    0x00001040, 0x00000000, 0x00000000, 0x10040040,
    0x10000040, 0x10001000, 0x00041040, 0x00040000,
    0x00041040, 0x00040000, 0x10041000, 0x00001000,
    0x00000040, 0x10040040, 0x00001000, 0x00041040,
    0x10001000, 0x00000040, 0x10000040, 0x10040000,
    0x10040040, 0x10000000, 0x00040000, 0x10001040,
    0x00000000, 0x10041040, 0x00040040, 0x10000040,
    0x10040000, 0x10001000, 0x10001040, 0x00000000,
    0x10041040, 0x00041000, 0x00041000, 0x00001040,
    0x00001040, 0x00040040, 0x10000000, 0x10041000],
]

def des_ip(data):
    l = struct.unpack(">I", data[:4])[0]
    r = struct.unpack(">I", data[4:])[0]

    T = ((l >>  4) ^ r) & 0x0F0F0F0F; r ^= T; l ^= (T <<  4)
    T = ((l >> 16) ^ r) & 0x0000FFFF; r ^= T; l ^= (T << 16)
    T = ((r >>  2) ^ l) & 0x33333333; l ^= T; r ^= (T <<  2)
    T = ((r >>  8) ^ l) & 0x00FF00FF; l ^= T; r ^= (T <<  8)
    r = ((r << 1) | (r >> 31)) & 0xFFFFFFFF
    T = (l ^ r) & 0xAAAAAAAA; r ^= T
    l ^= T
    l = ((l << 1) | (l >> 31)) & 0xFFFFFFFF

    return l,r



def hamming_weight(x):
    hw = 0
    while x:
        if x & 1:
            hw += 1
        x = x >> 1
    return hw


def des_predict(plain, sbox, k):
    l,r = des_ip(plain)

    rr = ((r << 28) | (r >> 4)) & 0xffffffff

    if sbox == 0:
        x = sboxes[sbox][((rr >> 24) ^ k) & 0x3f]
    if sbox == 1:
        x = sboxes[sbox][((r  >> 24) ^ k) & 0x3f]
    if sbox == 2:
        x = sboxes[sbox][((rr >> 16) ^ k) & 0x3f]
    if sbox == 3:
        x = sboxes[sbox][((r  >> 16) ^ k) & 0x3f]
    if sbox == 4:
        x = sboxes[sbox][((rr >>  8) ^ k) & 0x3f]
    if sbox == 5:
        x = sboxes[sbox][((r  >>  8) ^ k) & 0x3f]
    if sbox == 6:
        x = sboxes[sbox][((rr      ) ^ k) & 0x3f]
    if sbox == 7:
        x = sboxes[sbox][((r       ) ^ k) & 0x3f]
    
    return hamming_weight(x)
#des_predict("\xde\xad\xbe\xef\xde\xad\xbe\xef", 0, 2)
#sys.exit(1)

from random import *
def des_rand_challenge(count):
    ret = []
    for i in xrange(count):
        with open("/dev/urandom", "rb") as f:
            ret += [hexlify(f.read(8))]
        
    #ret = []
    #for i in xrange(count):
    #    ret += [choice(["0000000000000000", "1111111111111111", "aaaaaaaaaaaaaaaa", "7777777777777777", "ffffffffffffffff"])]
    return ret
    
import os
import traceback
import sys

from config import config_get, config_reload, args
from capture import *
from random import choice, randrange

class cpa:
    def __init__(self):
        self.trend = []
        self.n = 0
        self.X  = None
        self.XX = None
        self.XY = []
        self.YY = []
        self.Y  = []

    def add(self, trace, prediction):
        if self.n == 0:
            self.n  = 1
            self.X  = trace
            self.XX = trace * trace
            for p in prediction:
                self.XY += [trace * p]
                self.YY += [p*p]
                self.Y  += [p]
                self.trend += [[]]
        else:
            self.n  += 1
            self.X  += trace
            self.XX += trace * trace
            for i in xrange(len(prediction)):
                p = prediction[i]
                self.XY[i] += trace*p
                self.YY[i] += p*p
                self.Y[i]  += p


    def cpa(self):
        ret = []
        #computing pearson correlation coefficient
        for i in xrange(len(self.XY)):
            Z = self.n*self.XY[i] - self.X*self.Y[i]
            N = np.sqrt(self.n*self.XX - self.X**2) * np.sqrt(self.n*self.YY[i] - self.Y[i]**2)
            ret += [Z/N]
            np.save("%s/cpa-%d" % ("/tmp", i), Z/N)

        return ret

    def update_trend(self):
        if self.n < 2:
            return

        res = self.cpa()
        for i in xrange(len(res)):
            self.trend[i] += [np.max(res[i])]

            #plot(res[i],
            #    blocking=False,
            #    title="CFPA run %d" % cpa.n,
            #    f0=cap.demod_frequency,
            #    samp_rate=cap.demod_samp_rate,
            #    fft_step=128,
            #    png="/tmp/cpa-%d.png" % i)

        plot(np.array(self.trend),
            title="CFPA Trend run %d" % cpa.n,
            blocking=False,
            png="/tmp/cpa-trend.png")

    def show(self):
        if self.n < 2:
            return

        ret = []
        res = self.cpa()
        for i in xrange(len(res)):
            ret += [np.max(res[i])]

        plot(np.array(ret),
            title="CFPA run %d" % cpa.n,
            xlabel="Hypothesis",
            ylabel="",
            blocking=False,
            png="/tmp/cpa.png")

import glob
import os
def read_old_traces(path):
    files = glob.glob(path)
    shuffle(files)
    for fname in files[:10]:
        p,c,k = os.path.basename(fname).split("-")
        with open(fname, "rb") as f:
            data = f.read()
            trace = np.frombuffer(data, dtype=np.dtype('f4'))

        yield p, trace
        
            
if __name__ == "__main__":
    sbox = 0
    count = 30
    cpa = cpa()
    cap = capture()
    
    while True:
        for chal, trace in cap.capture(values=des_rand_challenge(count), count=count):
            s = stft(trace, 512, 64)
            s = cap.static_alignment_stft(s)
            sys.stderr.write(".")

            #compute prediction
            prediction = []
            for k in xrange(64):
                p = des_predict(unhexlify(chal), sbox, k)
                prediction += [p]
            cpa.add(s, prediction)
               
            #p = hamming_weight(struct.unpack("<Q", unhexlify(chal))[0])
            #p = des_predict(unhexlify(chal),0, 27)
            #cpa.add(s, [p])
        cpa.show()

        #plot(cpa.cpa()[0],
        #    blocking=False,
        #    title="CFPA run %d" % cpa.n,
        #    f0=cap.demod_frequency,
        #    samp_rate=cap.demod_samp_rate,
        #    fft_step=128,
        #    png="/tmp/cpa.png",)

