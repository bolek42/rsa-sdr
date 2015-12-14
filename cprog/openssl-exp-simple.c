#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <openssl/bn.h>
#include "common.h"

#define N 8000000
int main(int argc, char **argv)
{
    int i;
    BN_CTX *ctx = BN_CTX_new();
    BIGNUM *res = BN_new();
    BIGNUM *arg = BN_a2bn( argv[1]);
    BIGNUM *rand = BN_a2bn( rand_2048);
    BIGNUM *deadbeef = BN_a2bn( deadbeef_2048);

    //Dummyoperationen
    for ( i=0; i < N; i++) i ^= 0;

    //res = arg ^ rand  mod deadbeef
    BN_mod_exp_simple(res, arg, rand, deadbeef, ctx);
    //BN_mod_exp(res, arg, rand, deadbeef, ctx);

    //Dummyoperationen
    for ( i=0; i < N; i++) i^= 0;

    return 0;
}
