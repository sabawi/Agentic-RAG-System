#include <stdio.h>
#include <math.h>

int main() {
    int data[] = {10, 25, 30, 15, 40, 35, 20, 45, 50, 30};
    int n = sizeof(data) / sizeof(data[0]);
    
    printf("🔧 C Implementation Results\n");
    printf("==========================\n");
    
    // Calculate sum and average
    int sum = 0;
    for (int i = 0; i < n; i++) {
        sum += data[i];
    }
    
    double average = (double)sum / n;
    
    // Find min and max
    int min = data[0], max = data[0];
    for (int i = 1; i < n; i++) {
        if (data[i] < min) min = data[i];
        if (data[i] > max) max = data[i];
    }
    
    // Calculate standard deviation
    double variance = 0;
    for (int i = 0; i < n; i++) {
        variance += pow(data[i] - average, 2);
    }
    variance /= n;
    double std_dev = sqrt(variance);
    
    printf("Count: %d\n", n);
    printf("Sum: %d\n", sum);
    printf("Average: %.2f\n", average);
    printf("Min: %d\n", min);
    printf("Max: %d\n", max);
    printf("Standard Deviation: %.2f\n", std_dev);
    
    printf("\n✅ C implementation completed!\n");
    
    return 0;
}
