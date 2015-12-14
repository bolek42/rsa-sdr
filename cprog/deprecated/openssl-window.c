#include <openssl/bn.h>
#include <stdio.h>
#include <string.h>
#include "common.h"

#define N 1000000
#define WINDOWSIZE 32
int main(int argc, char **argv)
{
    int i, x=3;

    BN_CTX *ctx = BN_CTX_new();
    BIGNUM *in = BN_a2bn( argv[1]);
    BIGNUM *res = BN_a2bn( "01");
    BIGNUM *m = BN_a2bn( rand_4096);
    BIGNUM *val[WINDOWSIZE];
    val[0] = BN_a2bn( argv[1]);

    //dummy operation
    for (i = 0; i < N; i++) x = x*x;

    //create window
    for (i = 1; i < 32; i++) {
        val[i] = BN_CTX_get(ctx);
        BN_mod_mul(val[i], val[i-1], in, m, ctx);

        //char *s = BN_bn2hex(val[i]);
        //printf("%s\n\n", s);
    }

    //fake computation
    for (i = 1; i < 256; i++) {
        BN_mod_mul(res, res, res, m, ctx);
        BN_mod_mul(res, res, val[i % WINDOWSIZE], m, ctx);
        //BN_mod_mul(res, res, in, m, ctx);
    }

    //dummy operation
    for (i = 0; i < N; i++) x = x*x;


}
