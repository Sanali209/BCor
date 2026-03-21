import os


def is_comment_or_empty(line, in_multiline_comment):
    stripped = line.strip()
    if in_multiline_comment:
        if stripped.endswith('"""') or stripped.endswith("'''"):
            return True, False
        return True, True
    else:
        if not stripped or stripped.startswith('#'):
            return True, False
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if stripped.endswith('"""') and len(stripped) > 3:
                return True, False
            elif stripped.endswith("'''") and len(stripped) > 3:
                return True, False
            return True, True
    return False, False


def count_lines_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    in_multiline_comment = False
    code_lines = 0
    for line in lines:
        is_comment, in_multiline_comment = is_comment_or_empty(line, in_multiline_comment)
        if not is_comment:
            code_lines += 1
    return code_lines


def get_python_files(directory):
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files


def main(directory):
    python_files = get_python_files(directory)
    total_lines = 0
    for file in python_files:
        file_lines = count_lines_in_file(file)
        total_lines += file_lines
        print(f"{file}: {file_lines} lines")
    print(f"Total lines of code: {total_lines}")


if __name__ == "__main__":
    directory = input("Enter the directory to scan: ")
    main(directory)
