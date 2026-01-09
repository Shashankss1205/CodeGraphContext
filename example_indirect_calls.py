"""
Example file to demonstrate indirect function calls.
"""

def level_3_function():
    """Third level function - no calls"""
    print("Level 3")
    return "done"

def level_2_function():
    """Second level function - calls level_3"""
    result = level_3_function()
    return result

def level_1_function():
    """First level function - calls level_2"""
    data = level_2_function()
    return data

def main():
    """Main function - calls level_1"""
    output = level_1_function()
    print(output)

if __name__ == "__main__":
    main()
