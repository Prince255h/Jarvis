# STARK INDUSTRIES DYNAMICALLY SYNTHESIZED SKILL
# Created: 2026-11-01 15:31:26
# Purpose: Calculate the MD5 hash of the README.md file.

import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

import hashlib

def calculate_md5(file_path):
    md5_hash = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    except FileNotFoundError:
        return f"Error: File not found at {file_path}"
    except Exception as e:
        return f"An error occurred: {e}"

file_to_hash = 'README.md'
print(f"MD5 hash of {file_to_hash}: {calculate_md5(file_to_hash)}")