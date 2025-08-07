#!/usr/bin/env python3
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

print("\n✅ Results saved to analysis_results.json")
