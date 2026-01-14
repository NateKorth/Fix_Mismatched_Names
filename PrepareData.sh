#!/bin/bash

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
