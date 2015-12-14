
#include <openssl/bn.h>
#include <stdio.h>
#include <string.h>
#include "common.h"

#define N 8000000
#define M 1600
int main(int argc, char **argv)
{
    int i;

    BIGNUM *res = BN_a2bn( rand2_2048);
    BIGNUM *r = BN_a2bn( rand2_2048);
    BIGNUM *m = BN_a2bn( rand_2048);
    BIGNUM *arg = BN_a2bn( argv[1]);

    BN_CTX *ctx = BN_CTX_new();
    BN_MONT_CTX *mont = BN_MONT_CTX_new();
    BN_MONT_CTX_set(mont, m, ctx);

    //printf("%s\n", BN_bn2hex(&mont->RR));
    //printf("%d\n", mont->ri);
    //printf("%d\n", mont->Ni);

    BN_to_montgomery( arg, arg, mont, ctx);
    BN_to_montgomery( r, r, mont, ctx);

    //Dummyoperationen
    for ( i=0; i < N; i++) i ^= 0;

    //res = res * arg
    //for (i = 0; i < M; i++) BN_mod_mul(res, res, arg, m, ctx);
    for (i = 0; i < M; i++) BN_mod_mul_montgomery(res, res, arg, mont, ctx);

    //Dummyoperationen
    for ( i=0; i < N; i++) i ^= 0;
}
