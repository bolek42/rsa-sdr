CC=colorgcc -ggdb -O0 

all:
	$(CC) -o openssl-mul openssl-mul.c -lcrypto
	$(CC) -o openssl-mul-mont openssl-mul-mont.c -lcrypto
	$(CC) -o openssl-mul-time openssl-mul-time.c -lcrypto
	$(CC) -o openssl-mul-4096 openssl-mul-4096.c -lcrypto
	$(CC) -o openssl-exp openssl-exp.c -lcrypto
	$(CC) -o openssl-exp-simple openssl-exp-simple.c -lcrypto
	$(CC) -o openssl-exp-bin openssl-exp-bin.c bn_mod_exp_bin.c -lcrypto
	$(CC) -o openssl-exp-4096 openssl-exp-4096.c -lcrypto
	$(CC) -o openssl-exp-bin-4096 openssl-exp-bin-4096.c bn_mod_exp_bin.c -lcrypto
	$(CC) -o openssl-exp-dbg openssl-exp.c openssl-exp-dbg.c -lcrypto

clean:
	rm openssl-mul 2>/dev/null
	rm openssl-mul-mont 2>/dev/null
	rm openssl-mul-time 2>/dev/null
	rm openssl-mul-4096 2>/dev/null
	rm openssl-exp 2>/dev/null
	rm openssl-exp-bin 2>/dev/null
	rm openssl-exp-4096 2>/dev/null
	rm openssl-exp-bin-4096 2>/dev/null
	rm openssl-exp-simple 2>/dev/null
	rm openssl-exp-dbg 2>/dev/null

