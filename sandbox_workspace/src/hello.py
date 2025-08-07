#!/usr/bin/env python3
print("Hello from sandboxed Python!")
print("Current working directory:", __import__('os').getcwd())
print("Python version:", __import__('sys').version)

# Test basic computation
numbers = [1, 2, 3, 4, 5]
result = sum(x * x for x in numbers)
print(f"Sum of squares: {result}")

# Test file operations within sandbox
with open('output.txt', 'w') as f:
    f.write(f"Generated output: {result}\n")
    f.write("This file was created by Python script\n")

print("✅ Python script executed successfully!")
