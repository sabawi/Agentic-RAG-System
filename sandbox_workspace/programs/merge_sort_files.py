def merge_sort(arr):
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)


def merge(left, right):
    merged = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def main():
    import os

    num_files = int(input("Enter the number of files: "))
    file_names = []
    for i in range(num_files):
        file_name = input(f"Enter the name of file ")
        file_names.append(file_name)

    strings = []
    for file_name in file_names:
        if not os.path.exists(file_name):
            print(f"File not found. Skipping.")
            continue
        with open(file_name, 'r') as file:
            content = file.read()
            strings.extend(content.split('\n'))

    strings = merge_sort(strings)

    output_file = os.path.join('./programs', 'merged_sorted_output.txt')
    with open(output_file, 'w') as file:
        for string in strings:
            file.write(string + '\n')

    print(f"Sorted strings have been written to {output_file}")

if __name__ == "__main__":
    main()