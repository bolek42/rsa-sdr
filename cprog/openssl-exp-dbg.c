#include <openssl/bn.h>
#include <stdio.h>
#include <string.h>
//#include "common.h"

#define N 600
#define M 40

int BN_mod_exp_mont_dbg(BIGNUM *r, const BIGNUM *a, const BIGNUM *p,
                    const BIGNUM *m, BN_CTX *ctx, BN_MONT_CTX *in_mont);

    #define TABLE_SIZE      32
    #  define BN_window_bits_for_exponent_size(b) \
                    ((b) > 671 ? 6 : \
                     (b) > 239 ? 5 : \
                     (b) >  79 ? 4 : \
                     (b) >  23 ? 3 : 1)

    //Wrapper für BN_mod_exp_mont
    int BN_mod_exp(BIGNUM *r, const BIGNUM *a, const BIGNUM *p,
                        const BIGNUM *m, BN_CTX *ctx)
    {
        return BN_mod_exp_mont_dbg(r,a,p,m,ctx,NULL);
    }

    int BN_mod_exp_mont_dbg(BIGNUM *rr, const BIGNUM *a, const BIGNUM *p,
                        const BIGNUM *m, BN_CTX *ctx, BN_MONT_CTX *in_mont)
    {
        int i, j, bits, ret = 0, wstart, wend, window, wvalue;
        int start = 1;
        BIGNUM *d, *r;
        const BIGNUM *aa;
        /* Table of variables obtained from 'ctx' */
        BIGNUM *val[TABLE_SIZE];
        BN_MONT_CTX *mont = NULL;

        if (BN_get_flags(p, BN_FLG_CONSTTIME) != 0) {
            return BN_mod_exp_mont_consttime(rr, a, p, m, ctx, in_mont);
        }

        bn_check_top(a);
        bn_check_top(p);
        bn_check_top(m);

        //Im falle von RSA-CRT ist m=p eine Primzahl > 2 und damit ungerade
        if (!BN_is_odd(m)) {
            printf("BN_mod_exp_mont only supports odd mod\n");
            return (0);
        }
        bits = BN_num_bits(p);
        if (bits == 0) {
            ret = BN_one(rr);
            return ret;
        }

        BN_CTX_start(ctx);
        d = BN_CTX_get(ctx);
        r = BN_CTX_get(ctx);
        val[0] = BN_CTX_get(ctx);
        if (!d || !r || !val[0])
            goto err;

        /*
         * If this is not done, things will break in the montgomery part
         */

        if (in_mont != NULL)
            mont = in_mont;
        else {
            if ((mont = BN_MONT_CTX_new()) == NULL)
                goto err;
            if (!BN_MONT_CTX_set(mont, m, ctx))
                goto err;
        }

        //BN_ucmp vergleicht a und m nach ihren Wert
        //Dabei folgt a > m laut Dokumentation BN_ucmp(a, m) > 0
        if (a->neg || BN_ucmp(a, m) >= 0) {
            if (!BN_nnmod(val[0], a, m, ctx))
                goto err;
            aa = val[0];
        } else
            aa = a;
        if (BN_is_zero(aa)) {
        BN_zero(rr);
        ret = 1;
        goto err;
    }
    if (!BN_to_montgomery(val[0], aa, mont, ctx))
        goto err;               /* 1 */

    window = BN_window_bits_for_exponent_size(bits);
    if (window > 1) {
        if (!BN_mod_mul_montgomery(d, val[0], val[0], mont, ctx))
            goto err;           /* 2 */
        //Vorberechnung der Potenzen
        printf( "a = %s\n", BN_bn2hex(a));
        printf( "window[0] = %s\n", BN_bn2hex(val[0]));
        j = 1 << (window - 1);
        for (i = 1; i < j; i++) {
            if (((val[i] = BN_CTX_get(ctx)) == NULL) ||
                !BN_mod_mul_montgomery(val[i], val[i - 1], d, mont, ctx))
                goto err;
            printf( "window[%d] = %s\n", i,  BN_bn2hex(val[i-1]));
        }
    }

    start = 1;                  /* This is used to avoid multiplication etc
                                 * when there is only the value '1' in the
                                 * buffer. */
    wvalue = 0;                 /* The 'value' of the window */
    wstart = bits - 1;          /* The top bit of the window */
    wend = 0;                   /* The bottom bit of the window */

#if 1                           /* by Shay Gueron's suggestion */
    j = m->top;                 /* borrow j */
    if (m->d[j - 1] & (((BN_ULONG)1) << (BN_BITS2 - 1))) {
        if (bn_wexpand(r, j) == NULL)
            goto err;
        /* 2^(top*BN_BITS2) - m */
        r->d[0] = (0 - m->d[0]) & BN_MASK2;
        for (i = 1; i < j; i++)
            r->d[i] = (~m->d[i]) & BN_MASK2;
        r->top = j;
        /*
         * Upper words will be zero if the corresponding words of 'm' were
         * 0xfff[...], so decrement r->top accordingly.
         */
        bn_correct_top(r);
    } else
#endif
    if (!BN_to_montgomery(r, BN_value_one(), mont, ctx))
        goto err;

    printf("Access to window Array:\n");

    for (;;) {
        if (BN_is_bit_set(p, wstart) == 0) {
            if (!start) {
                if (!BN_mod_mul_montgomery(r, r, r, mont, ctx))
                    goto err;
            }
            if (wstart == 0)
                break;
            wstart--;
            continue;
        }
        /*
         * We now have wstart on a 'set' bit, we now need to work out how bit
         * a window to do.  To do this we need to scan forward until the last
         * set bit before the end of the window
         */
        j = wstart;
        wvalue = 1;
        wend = 0;
        for (i = 1; i < window; i++) {
            if (wstart - i < 0)
                break;
            if (BN_is_bit_set(p, wstart - i)) {
                wvalue <<= (i - wend);
                wvalue |= 1;
                wend = i;
            }
        }

        /* wend is the size of the current window */
        j = wend + 1;
        /* add the 'bytes above' */
        if (!start)
            for (i = 0; i < j; i++) {
                if (!BN_mod_mul_montgomery(r, r, r, mont, ctx))
                    goto err;
            }

        /* wvalue will be an odd number < 2^window */
        if (!BN_mod_mul_montgomery(r, r, val[wvalue >> 1], mont, ctx))
            goto err;

        //wvalue >> 1 ist der Index fuer den zugriff auf das Fenster
        printf("%02x ", wvalue >> 1);

        /* move the 'window' down further */
        wstart -= wend + 1;
        wvalue = 0;
        start = 0;
        if (wstart < 0)
            break;
    }
    printf("\n");
#if defined(SPARC_T4_MONT)
    if (OPENSSL_sparcv9cap_P[0] & (SPARCV9_VIS3 | SPARCV9_PREFER_FPU)) {
        j = mont->N.top;        /* borrow j */
        val[0]->d[0] = 1;       /* borrow val[0] */
        for (i = 1; i < j; i++)
            val[0]->d[i] = 0;
        val[0]->top = j;
        if (!BN_mod_mul_montgomery(rr, r, val[0], mont, ctx))
            goto err;
    } else
#endif
    if (!BN_from_montgomery(rr, r, mont, ctx))
        goto err;
    ret = 1;
 err:
    if ((in_mont == NULL) && (mont != NULL))
        BN_MONT_CTX_free(mont);
    BN_CTX_end(ctx);
    bn_check_top(rr);
    return (ret);
}
