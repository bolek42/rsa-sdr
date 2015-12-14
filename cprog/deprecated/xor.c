#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#define N 2000000
int main(int argc, char **argv){
    uint32_t i, a, arg;

    arg = strtol(argv[1], NULL, 0);
#if 1
    for (i = 0; i < 4*N; i++) a ^= 0;
#endif

    for (i = 0; i < N; i++) a ^= 0;
    for (i = 0; i < N; i++) a ^= arg;
    for (i = 0; i < N; i++) a ^= 0;
}
