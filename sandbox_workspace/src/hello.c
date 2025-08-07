#include <stdio.h>
#include <stdlib.h>

int main() {
    printf("Hello from sandboxed C program!\n");
    printf("Testing basic operations...\n");
    
    int sum = 0;
    for (int i = 1; i <= 10; i++) {
        sum += i;
    }
    
    printf("Sum of 1-10: %d\n", sum);
    
    // Create output file
    FILE *fp = fopen("c_output.txt", "w");
    if (fp != NULL) {
        fprintf(fp, "C program output: %d\n", sum);
        fclose(fp);
        printf("Output file created successfully\n");
    }
    
    return 0;
}
