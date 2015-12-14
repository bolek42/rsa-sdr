    def demod_fft(trace, f, f0, samp_rate, fft_len=16, fft_step=8):
        ##calculate trigger_bin from trigger_frequency
        trigger_bin = stft_f2bin(f, f0, fft_len, samp_rate)
        if trigger_bin < 0 or trigger_bin >= fft_len:
            return None

        s = stft(trace, fft_len, fft_step)
        trig = np.zeros(len(s))

        for i in xrange(len(s)):
            trig[i] = s[i,trigger_bin]

        return trig

