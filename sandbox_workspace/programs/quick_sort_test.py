def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

# Test datasets
datasets = [
    [3, 6, 8, 10, 15, 23, 30],
    [10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
    [1, 2, 3, 4, 5],
    [5, 4, 3, 2, 1],
    [1, 1, 1, 1, 1],
    [100, 200, 300, 400, 500],
    [500, 400, 300, 200, 100],
    [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
    [100, 90, 80, 70, 60, 50, 40, 30, 20, 10],
    [1, 3, 5, 7, 9, 2, 4, 6, 8, 10]
]

# Run tests
for dataset in datasets:
    print(f"Original: {dataset}")
    sorted_data = quick_sort(dataset)
    print(f"Sorted: {sorted_data}\n")