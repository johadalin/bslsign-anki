import argparse
from pathlib import Path
import os
from pprint import pprint

def check_file_for_duplicates(filename):
    duplicates = []
    with open(filename, 'r') as f:
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
            pprint(duplicate)
        return 1
    else:
        return 0

def check_other_txt_for_duplicates(reference_file):
    # Read words from the reference file
    with open(reference_file, 'r', encoding='utf-8') as f:
        reference_words = set(word.strip() for word in f if word.strip())

    # Get the directory and list of files
    directory = os.path.dirname(os.path.abspath(reference_file))
    all_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    all_wordlist_files = [f for f in all_files if 'wordlist' in f]

    # Prepare results
    duplicates = {word: [] for word in reference_words}

    for filename in all_wordlist_files:
        if filename == os.path.basename(reference_file):
            continue  # Skip the reference file itself

        file_path = os.path.join(directory, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_words = set(word.strip().replace('*','') for word in f if word.strip())
                for word in reference_words:
                    if word in file_words:
                        duplicates[word].append(filename)
        except Exception as e:
            print(f"Could not read {filename}: {e}")

    # Filter out words that were not duplicated
    duplicates = {word: files for word, files in duplicates.items() if files}
    pprint(duplicates)
    return duplicates



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', required=True)
    args = parser.parse_args()
    if check_file_for_duplicates(args.filename):
        print(f"ERROR: duplicate entry in file {args.filename}")
    check_other_txt_for_duplicates(args.filename)
