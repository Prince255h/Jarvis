# STARK INDUSTRIES DYNAMICALLY SYNTHESIZED SKILL
# Created: 2026-11-01 15:28:05
# Purpose: Counts all Python files in a specified directory and its subdirectories, then calculates their total line count.

import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

import os
from pathlib import Path

def count_python_files_and_lines(directory_path):
    """
    Counts Python files and their total lines in the specified directory and its subdirectories.
    """
    python_file_count = 0
    total_line_count = 0
    target_dir = Path(directory_path)

    print(f"J.A.R.V.I.S. Initiating scan for Python files in: {target_dir}")

    if not target_dir.exists():
        print(f"Error: Directory '{directory_path}' does not exist. Please ensure the path is correct, sir.")
        return

    if not target_dir.is_dir():
        print(f"Error: Path '{directory_path}' is not a directory. Please provide a valid directory path, sir.")
        return

    try:
        # rglob recursively finds all files matching the pattern
        for file_path in target_dir.rglob("*.py"):
            if file_path.is_file(): # Ensure it's a file and not a directory named like a .py file
                python_file_count += 1
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        # Read lines and count them, ignoring potential decoding errors
                        lines = f.readlines()
                        total_line_count += len(lines)
                    print(f"  - Processed '{file_path.relative_to(target_dir)}': {len(lines)} lines")
                except IOError as e:
                    print(f"  - Warning: Could not read file '{file_path}': {e}")
                except Exception as e:
                    print(f"  - An unexpected error occurred with file '{file_path}': {e}")

        print(f"\n--- Scan Complete ---")
        print(f"Total Python files found in '{target_dir}': {python_file_count}")
        print(f"Total lines across all Python files: {total_line_count}")

    except Exception as e:
        print(f"An error occurred during the directory scan: {e}")

if __name__ == "__main__":
    target_directory = "g:/Jarvis"
    count_python_files_and_lines(target_directory)