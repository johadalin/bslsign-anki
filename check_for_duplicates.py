import argparse
from pathlib import Path
from os import system
from os.path import exists


def check_file_for_duplicates(args):
    duplicates = []
    with open(args.filename, 'r') as f:
        seen = set()
        for line in f:
            line_lower = line.lower()
            if line_lower in seen:
                duplicates.append(line_lower)
            else:
                seen.add(line_lower)

    if duplicates:
        print(f"Duplicates found:")
        for duplicate in duplicates:
            print(duplicate)
        return 1
    else:
        return 0

def check_other_txt_for_duplicates(args):
    return 0



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', required=True)
    args = parser.parse_args()
    if check_file_for_duplicates(args):
        print(f"ERROR: duplicate entry in file {args.filename}")
    if check_other_txt_for_duplicates(args):
        print(f"ERROR: duplicate entries found")
