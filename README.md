# Fix_Mismatched_Names
It's happened to everyone. The names in the phenotype data you got from collaboratorA doesn't match the names in the genotype file from LabB. Here's an automated answer to this problem. It's designed for a .csv file with all the names in your metadata and to pull the genotype header from a vcf file. But can be adapted to compare any list of names

## Get two lists of mismatching names (bash)
```
VCF_FILE="./path/to/your/file/file.vcf.gz"
CSV_FILE="./path/to/your/file/listofnames.csv"

echo "Processing $VCF_FILE and $CSV_FILE..."

# --- Step 1: Process the CSV File ---
# 1. tail -n +2: Skip the header line ("Genotype")
# 2. tr -d '\r': Remove weird Windows carriage returns just in case
# 3. sort: Sort the list (required for 'comm')
tail -n +2 "$CSV_FILE" | tr -d '\r' | sort > sorted_csv_list.tmp

echo "Found $(wc -l < sorted_csv_list.tmp) samples in CSV file."

# --- Step 2: Extract Sample Names from VCF (Without unzipping) ---
# 1. zgrep ...: Finds the header line starting with #CHROM
# 2. cut -f 10-: Keeps columns 10 to the end (where sample names are in VCFs)
# 3. tr '\t' '\n': Converts tab-separated row into a column list
# 4. sort: Sort the list
zgrep -m1 "^#CHROM" "$VCF_FILE" | cut -f 10- | tr '\t' '\n' | sort > sorted_vcf_list.tmp

echo "Found $(wc -l < sorted_vcf_list.tmp) samples in VCF file."

# --- Step 3: Compare Lists ---

# Generate NotInData.csv
# Samples present in VCF (file 1) but NOT in CSV (file 2)
# -23: Suppress lines unique to file 2 and lines common to both
echo "Genotype" > NotInData.csv
comm -23 sorted_vcf_list.tmp sorted_csv_list.tmp >> NotInData.csv

# Generate NotInSNPs.csv
# Samples present in CSV (file 2) but NOT in VCF (file 1)
# -13: Suppress lines unique to file 1 and lines common to both
echo "Genotype" > NotInSNPs.csv
comm -13 sorted_vcf_list.tmp sorted_csv_list.tmp >> NotInSNPs.csv

# --- Cleanup ---
rm sorted_csv_list.tmp sorted_vcf_list.tmp

echo "------------------------------------------------"
echo "Done!"
echo "1. NotInData.csv (In VCF, missing from your CSV)"
echo "2. NotInSNPs.csv (In your CSV, missing from VCF)"
```

## Compare the two lists (python3)
```
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
```
This will generate a new csv file with the name in your data and it's potential match in the vcf file. From here you need to check it, so this is semi-manual, but still a lot better than A) looking through every genotype 1-by-1 or B) Trusting a script to compare every case

Enjoy! comments and questions to nate.korthATgmail.com
