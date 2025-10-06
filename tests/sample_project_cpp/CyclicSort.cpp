#include <iostream>
using namespace std;

void cyclicSort(int arr[], int n) {
    int i = 0;
    while (i < n) {
        int correctIndex = arr[i] - 1;

        if (arr[i] != arr[correctIndex]) {
            // Swap arr[i] and arr[correctIndex]
            swap(arr[i], arr[correctIndex]);
        } else {
            i++;
        }
    }
}

void printArray(int arr[], int n) {
    for (int i = 0; i < n; i++)
        cout << arr[i] << " ";
    cout << endl;
}

int main() {
    int arr[] = {3, 5, 2, 1, 4};
    int n = sizeof(arr) / sizeof(arr[0]);

    cout << "Before sorting: ";
    printArray(arr, n);

    cyclicSort(arr, n);

    cout << "After sorting: ";
    printArray(arr, n);

    return 0;
}
