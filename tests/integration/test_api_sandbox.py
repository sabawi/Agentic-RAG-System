#!/usr/bin/env python3
"""
Test the Sandboxed Executor through the FastAPI API
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from user_tools.sandboxed_executor import SandboxedExecutorTool

async def demo_sandboxed_code_execution():
    print("🚀 Sandboxed Code Execution Demo")
    print("=" * 50)
    
    tool = SandboxedExecutorTool()
    
    # Demo 1: Create a data analysis script
    print("\n📊 DEMO 1: Create Python data analysis script")
    
    analysis_code = '''#!/usr/bin/env python3
"""
Simple data analysis demonstration
"""
import math
import json

# Sample data analysis
data = [10, 25, 30, 15, 40, 35, 20, 45, 50, 30]
print("📊 Data Analysis Results")
print("=" * 30)
print(f"Dataset: {data}")
print(f"Count: {len(data)}")
print(f"Sum: {sum(data)}")
print(f"Average: {sum(data)/len(data):.2f}")
print(f"Min: {min(data)}")
print(f"Max: {max(data)}")

# Calculate standard deviation
mean = sum(data) / len(data)
variance = sum((x - mean) ** 2 for x in data) / len(data)
std_dev = math.sqrt(variance)
print(f"Standard Deviation: {std_dev:.2f}")

# Save results to JSON
results = {
    "dataset": data,
    "statistics": {
        "count": len(data),
        "sum": sum(data),
        "average": sum(data)/len(data),
        "min": min(data),
        "max": max(data),
        "std_dev": std_dev
    }
}

with open("analysis_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\\n✅ Results saved to analysis_results.json")
'''
    
    result = await tool.execute(
        action="create_file",
        filename="src/data_analysis.py",
        content=analysis_code
    )
    print(f"✅ Script created: {result['success']}")
    
    # Demo 2: Execute the data analysis
    print("\n🔍 DEMO 2: Execute data analysis")
    result = await tool.execute(
        action="run_code",
        filename="src/data_analysis.py",
        language="python"
    )
    
    if result['success']:
        print("📤 Output:")
        print(result['result']['stdout'])
        print(f"⏱️ Execution time: {result['result']['execution_time']}s")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Demo 3: Read the generated JSON file
    print("\n📄 DEMO 3: Read generated results")
    result = await tool.execute(
        action="read_file",
        filename="analysis_results.json"
    )
    
    if result['success']:
        print("📊 Analysis Results JSON:")
        print(result['result']['content'])
    else:
        print(f"❌ Error: {result['error']}")
    
    # Demo 4: Create and run a simple C program for comparison
    print("\n🔧 DEMO 4: C program for performance comparison")
    
    c_code = '''#include <stdio.h>
#include <math.h>

int main() {
    int data[] = {10, 25, 30, 15, 40, 35, 20, 45, 50, 30};
    int n = sizeof(data) / sizeof(data[0]);
    
    printf("🔧 C Implementation Results\\n");
    printf("==========================\\n");
    
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
    
    printf("Count: %d\\n", n);
    printf("Sum: %d\\n", sum);
    printf("Average: %.2f\\n", average);
    printf("Min: %d\\n", min);
    printf("Max: %d\\n", max);
    printf("Standard Deviation: %.2f\\n", std_dev);
    
    printf("\\n✅ C implementation completed!\\n");
    
    return 0;
}
'''
    
    result = await tool.execute(
        action="create_file",
        filename="src/analysis.c",
        content=c_code
    )
    print(f"✅ C file created: {result['success']}")
    
    if result['success']:
        result = await tool.execute(
            action="run_code",
            filename="src/analysis.c",
            language="c"
        )
        
        if result['success']:
            print("📤 C Output:")
            print(result['result']['stdout'])
            print(f"⏱️ C Execution time: {result['result']['execution_time']}s")
        else:
            print(f"❌ C Error: {result['error']}")
    
    # Demo 5: List all created files
    print("\n📁 DEMO 5: Final sandbox contents")
    result = await tool.execute(action="list_files")
    if result['success']:
        files = result['result']['files']
        print(f"📊 Total files: {len(files)}")
        for file in files:
            print(f"  📄 {file['name']} ({file['type']}, {file['size_bytes']} bytes)")
    
    print("\n" + "=" * 50)
    print("🎉 Sandboxed Execution Demo Complete!")
    print("🔒 All operations performed safely within sandbox")
    print("📈 Ready for LLM-driven code execution and analysis")

if __name__ == "__main__":
    asyncio.run(demo_sandboxed_code_execution())