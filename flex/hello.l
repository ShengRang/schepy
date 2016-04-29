%{

#include "stdio.h"
#include <stdlib.h>
int count = 0;
%}
digit [0-9]
number {digit}+
%%
{number} { int n = atoi (yytext);
    printf("^%d^", n);
    if(n>9) count++;
}
%%
int main()
{
        yylex();
        fprintf(stderr, "number of fuck = %d", count);
}
