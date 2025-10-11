def greet(name):
    print(f"Hello, {name}!")

def factorial(n):
    result = 1
    for i in range(1, n+1):
        result *= i
    return result

def nested_condition(x):
    if x > 0:
        if x % 2 == 0:
            print("Positive even")
        else:
            print("Positive odd")
    else:
        print("Non-positive")
