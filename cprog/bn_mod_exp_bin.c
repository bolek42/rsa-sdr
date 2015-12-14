#include <openssl/bn.h>
#include <openssl/err.h>

int BN_mod_exp_bin(BIGNUM *r, BIGNUM *a, const BIGNUM *p, const BIGNUM *m, BN_CTX *ctx)
{
    int i, bits, ret = 0;
    BIGNUM *v, *rr;

    if (BN_get_flags(p, BN_FLG_CONSTTIME) != 0) {
        /* BN_FLG_CONSTTIME only supported by BN_mod_exp_mont() */
        BNerr(BN_F_BN_EXP, ERR_R_SHOULD_NOT_HAVE_BEEN_CALLED);
        return -1;
    }

    BN_CTX_start(ctx);
    if ((r == a) || (r == p))
        rr = BN_CTX_get(ctx);
    else
        rr = r;
    v = BN_CTX_get(ctx);
    if (rr == NULL || v == NULL)
        goto err;

    if (!BN_nnmod(a, a, m, ctx))
        goto err;               /* 1 */

    if (BN_copy(v, a) == NULL)
        goto err;
    bits = BN_num_bits(p);

    if (BN_is_odd(p)) {
        if (BN_copy(rr, a) == NULL)
            goto err;
    } else {
        if (!BN_one(rr))
            goto err;
    }

    for (i = 1; i < bits; i++) {
        if (!BN_mod_sqr(v, v, m, ctx))
            goto err;
        if (BN_is_bit_set(p, i)) {
            if (!BN_mod_mul(rr, rr, v, m,ctx))
                goto err;
        }
    }
    if (r != rr)
        BN_copy(r, rr);
    ret = 1;
 err:
    BN_CTX_end(ctx);
    bn_check_top(r);
    return (ret);
}
