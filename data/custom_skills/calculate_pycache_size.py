# STARK INDUSTRIES DYNAMICALLY SYNTHESIZED SKILL
# Created: 2026-11-01 15:31:45
# Purpose: Calculate the total disk space occupied by all __pycache__ folders within a specified directory.

import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

import os

def get_folder_size(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

root_dir = 'g:/Jarvis'
total_pycache_size = 0

print(f"Scanning for __pycache__ folders in: {root_dir}")

for dirpath, dirnames, filenames in os.walk(root_dir):
    if '__pycache__' in dirnames:
        pycache_path = os.path.join(dirpath, '__pycache__')
        try:
            size = get_folder_size(pycache_path)
            total_pycache_size += size
            print(f"Found __pycache__ at {pycache_path}: {size / (1024*1024):.2f} MB")
        except PermissionError:
            print(f"Permission denied for {pycache_path}, skipping.")
        except Exception as e:
            print(f"Error processing {pycache_path}: {e}")

def format_bytes(size):
    # 2**10 = 1024
    power = 2**10
    n = 0
    labels = {0 : 'Bytes', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {labels[n]}"

print(f"\nTotal size of all __pycache__ folders: {format_bytes(total_pycache_size)}")