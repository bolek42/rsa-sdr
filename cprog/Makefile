CC=colorgcc -ggdb -O0 

all:
	$(CC) -o openssl-mul openssl-mul.c -lcrypto
	$(CC) -o openssl-mul-4096 openssl-mul-4096.c -lcrypto
	$(CC) -o openssl-exp openssl-exp.c -lcrypto
	$(CC) -o openssl-exp-dbg openssl-exp.c openssl-exp-dbg.c -lcrypto

clean:
	rm openssl-mul 2>/dev/null
	rm openssl-mul-4096 2>/dev/null
	rm openssl-exp 2>/dev/null
	rm openssl-exp-dbg 2>/dev/null

