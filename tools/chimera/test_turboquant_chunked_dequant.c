/* Numeric CPU invariant for Cloud9 native TurboQuant KV.
 * Not a GPU quality claim: verify per-block dequant is identical when chunked.
 */
#include "ggml.h"
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int verify(enum ggml_type type, const char *name, int64_t k) {
    const struct ggml_type_traits * tr=ggml_get_type_traits(type);
    if (!tr || !tr->to_float || tr->blck_size<=0 || k % tr->blck_size) return -2;
    const size_t qbytes=ggml_row_size(type,k);
    float * x=malloc((size_t)k*sizeof(float));
    float * all=malloc((size_t)k*sizeof(float));
    float * pieces=malloc((size_t)k*sizeof(float));
    void * q=malloc(qbytes);
    if (!x || !all || !pieces || !q) return -3;
    for(int64_t i=0;i<k;++i)x[i]=3.0f*sinf((float)i*0.037f);
    ggml_quantize_init(type);
    ggml_quantize_chunk(type,x,q,0,1,k,NULL);
    tr->to_float(q,all,k);
    const int64_t step=(256/tr->blck_size)*tr->blck_size;
    if(step<=0)return -4;
    const char *pq=q;
    for(int64_t i=0;i<k;i+=step){
        int64_t n=(step<k-i)?step:k-i;
        tr->to_float(pq,pieces+i,n);
        pq+=(n/tr->blck_size)*tr->type_size;
    }
    int mismatch=memcmp(all,pieces,(size_t)k*sizeof(float))!=0;
    int nonfinite=0;
    for(int64_t i=0;i<k;i++)if(!isfinite(all[i]))nonfinite=1;
    printf("%s k=%lld blocks=%lld chunk=%lld valid=%d\n",name,(long long)k,(long long)tr->blck_size,(long long)step,!mismatch&&!nonfinite);
    free(x);free(all);free(pieces);free(q);
    return mismatch || nonfinite;
}

int main(void){
    struct item{enum ggml_type type;const char *name;} cases[]={
        {GGML_TYPE_TURBO2_0,"turbo2"},
        {GGML_TYPE_TURBO3_0,"turbo3"},
        {GGML_TYPE_TURBO4_0,"turbo4"}
    };
    int64_t lengths[]={128,256,384,512,4096};
    int failures=0;
    for(size_t c=0;c<sizeof(cases)/sizeof(cases[0]);c++)
        for(size_t n=0;n<sizeof(lengths)/sizeof(lengths[0]);n++)
            failures+=verify(cases[c].type,cases[c].name,lengths[n])!=0;
    printf("TURBO_KV_CHUNKED_NUMERIC %d/15 %s\n",15-failures,failures?"FAIL":"PASS");
    return failures?1:0;
}
