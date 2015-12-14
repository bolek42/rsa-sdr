#include <openssl/bn.h>
#include <stdio.h>
#include <string.h>
#include "common.h"

//Unmodified Square and Multiply Algorithm
//res = a^b mod m
BIGNUM *square_and_multiply( BIGNUM *a, BIGNUM *b, BIGNUM *m, BN_CTX *ctx)
{
    int i, n;
    BIGNUM *res =  BN_CTX_get(ctx);
    BIGNUM *t =  BN_CTX_get(ctx);
    BIGNUM *tmp;
    BN_one(res);

    n = BN_num_bits(b);
    for( i=0; i < n; i ++)
    {
        BN_mod_mul(res, res, res, m, ctx);

        if ( BN_is_bit_set( b, n - i - 1 ))
        {
            BN_mod_mul(t, res, a, m, ctx);
            tmp = t;
            t = res;
            res = tmp;
        }

    }

    return res;
}

#define WINDOWSIZE 32
int main(int argc, char **argv)
{
    BN_CTX *ctx = BN_CTX_new();
    BIGNUM *a = BN_a2bn( argv[1]);
    BIGNUM *b = BN_a2bn( exp);//argv[2]);
    BIGNUM *m = BN_a2bn( rand_m);
    BIGNUM *res = square_and_multiply( a,b,m,ctx);
    int j,c;
    //for (j=0; j<4000000; j++) c^=0;

    //char *s = BN_bn2hex(res);
    //printf("%s\n", s);

}
