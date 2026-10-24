/* Actual Turbo2/3/4 CPU quant/dequant plus inverse signed WHT.
 * Quality smoke for native Cloud9 KV; NOT a GPU attention certification.
 */
#include "ggml.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

extern const float * ggml_turbo_wht_signs1(void);
extern const float * ggml_turbo_wht_signs2(void);

static void invert_wht_128(float * x) {
    const float * s1=ggml_turbo_wht_signs1();
    const float * s2=ggml_turbo_wht_signs2();
    for(int i=0;i<128;i++)x[i]*=s2[i];
    for(int h=1;h<128;h*=2)for(int i=0;i<128;i+=2*h)for(int j=i;j<i+h;j++){
        float a=x[j],b=x[j+h];
        x[j]=a+b;
        x[j+h]=a-b;
    }
    for(int i=0;i<128;i++)x[i]*=s1[i]*0.08838834764831845f;
}
static int test_case(enum ggml_type type,const char * name,int scenario) {
    float input[128],output[128],compressed_domain[128];
    for(int i=0;i<128;i++){
        switch(scenario) {
            case 0: input[i]=(i==0)?1.0f:0.0f; break;
            case 1: input[i]=sinf(i*0.117f)*3.0f+cosf(i*0.31f)*0.5f; break;
            default: input[i]=cosf(i*0.2f+0.6f)*7.0f; break;
        }
    }
    size_t n=ggml_row_size(type,128);
    void * q=malloc(n);
    if(!q)return 1;
    ggml_quantize_init(type);
    ggml_quantize_chunk(type,input,q,0,1,128,NULL);
    ggml_get_type_traits(type)->to_float(q,compressed_domain,128);
    memcpy(output,compressed_domain,sizeof(output));
    invert_wht_128(output);
    double dot=0,ni=0,no=0,err=0;
    for(int i=0;i<128;i++){
        if(!isfinite(output[i])){free(q);return 2;}
        dot+=(double)input[i]*output[i];
        ni+=(double)input[i]*input[i];
        no+=(double)output[i]*output[i];
        double diff=input[i]-output[i];
        err+=diff*diff;
    }
    double cosine=(ni>0&&no>0)?dot/sqrt(ni*no):0;
    double mse=err/128;
    /* Conservative quality floors calibrated against actual compiled Cloud9
     * CPU codec, NOT a surrogate for cross-context language-model quality.
     * Fail when a future codec change materially corrupts WHT inversion. */
    const double minimum_cosine =
        type==GGML_TYPE_TURBO2_0 ? 0.90 :
        type==GGML_TYPE_TURBO3_0 ? 0.97 : 0.98;
    const int ok=isfinite(cosine) && cosine>=minimum_cosine;
    printf("%s scenario=%d cosine=%.6f min=%.3f mse=%.7f bytes=%zu %s\n",
           name,scenario,cosine,minimum_cosine,mse,n,ok?"PASS":"FAIL");
    free(q);
    return !ok;
}
int main(void){
    struct entry{enum ggml_type type;const char *name;} m[]={
        {GGML_TYPE_TURBO2_0,"turbo2"}, {GGML_TYPE_TURBO3_0,"turbo3"},
        {GGML_TYPE_TURBO4_0,"turbo4"}
    };
    int failures=0;
    for(int j=0;j<3;j++)for(int i=0;i<3;i++)
        failures+=test_case(m[j].type,m[j].name,i);
    printf("TURBO_KV_WHT_RECONSTRUCTION %d/9 %s\n",9-failures,failures?"FAIL":"PASS");
    return failures!=0;
}
