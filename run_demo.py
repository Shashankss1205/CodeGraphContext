import os
from lizard import analyze_file

# Path to the 'examples' folder
examples_dir = os.path.join(os.getcwd(), 'examples')

# Analyze all Python files in the 'examples' folder
for filename in os.listdir(examples_dir):
    if filename.endswith('.py'):
        file_path = os.path.join(examples_dir, filename)
        print(f"\nAnalyzing {filename}...\n")
        result = analyze_file(file_path)
        for func in result.function_list:
            print(f"Function: {func.name}, Start Line: {func.start_line}, "
                  f"Complexity: {func.cyclomatic_complexity}, "
                  f"Length: {func.length}")
