import csv
import difflib
import re

# --- Configuration ---
# Your "bad" names (In your CSV, but not in VCF)
input_bad_names = "NotInSNPs.csv"
# The "target" names (In VCF, but not in your CSV)
input_valid_names = "NotInData.csv"
output_file = "Suggested_Matches.csv"

# --- Helper Function to Clean Strings ---
def clean_string(s):
    # Removes anything that isn't a letter or number (removes _ - . etc)
    return re.sub(r'[^a-zA-Z0-9]', '', s).lower()

# --- Load Data ---
print("Loading files...")

# Read the valid VCF names into a list
with open(input_valid_names, 'r') as f:
    # skip header
    valid_names = [line.strip() for line in f.readlines()[1:] if line.strip()]

# Read your "bad" names
with open(input_bad_names, 'r') as f:
    bad_names = [line.strip() for line in f.readlines()[1:] if line.strip()]

results = []

print(f"Comparing {len(bad_names)} unmatched samples against {len(valid_names)} available VCF options...")

# --- Matching Logic ---
for bad in bad_names:
    best_match = None
    match_type = "No Match"
    score = 0.0

    # 1. Exact Match (Case Insensitive)
    # We look for a valid name that matches 'bad' if we ignore case
    for valid in valid_names:
        if bad.lower() == valid.lower():
            best_match = valid
            match_type = "Case Difference"
            score = 1.0
            break

    # 2. Clean Match (Ignore punctuation like _ or -)
    if not best_match:
        bad_clean = clean_string(bad)
        for valid in valid_names:
            if bad_clean == clean_string(valid):
                best_match = valid
                match_type = "Format Difference (e.g. _ or -)"
                score = 0.95
                break

    # 3. Fuzzy Match (Levenshtein Distance)
    if not best_match:
        # Get the single closest match if it is at least 60% similar
        matches = difflib.get_close_matches(bad, valid_names, n=1, cutoff=0.6)
        if matches:
            best_match = matches[0]
            match_type = "Fuzzy Match"
            # Calculate a similarity ratio for your review
            score = difflib.SequenceMatcher(None, bad, best_match).ratio()

    # --- Save Result ---
    if best_match:
        results.append([bad, best_match, match_type, f"{score:.2f}"])

# --- Write Output ---
with open(output_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["My_Genotype", "VCF_Genotype", "Reason", "Confidence_Score"])
    writer.writerows(results)

print("------------------------------------------------")
print(f"Done! Found {len(results)} potential matches.")
print(f"Please review '{output_file}' before applying changes.")
