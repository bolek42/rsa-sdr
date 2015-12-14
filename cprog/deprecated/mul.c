#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#define N 2000000
int main(int argc, char **argv){
    uint32_t i, a, arg;
    float x = 3;

    a = 1;
    arg = strtol(argv[1], NULL, 0);

    for (i = 0; i < 4*N; i++)
        a ^= 0;

    for (i = 0; i < N; i++) {
        if (arg) a *= 0x34543289;
        else     a ^= 0;
    }

    for (i = 0; i < N; i++)
        a ^= 0;


}
