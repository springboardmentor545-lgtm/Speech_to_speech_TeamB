import csv
import os

INPUT_CSV = "transcripts/transcripts.csv"
OUTPUT_CSV = "transcripts/transcripts_clean.csv"

def fix_csv_encoding():
    """Fix UTF-8 encoding issues and create clean CSV for Excel"""
    
    if not os.path.exists(INPUT_CSV):
        print(f"Error: {INPUT_CSV} not found!")
        return
    
    # Read original CSV with UTF-8
    with open(INPUT_CSV, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        rows = list(reader)
    
    # Write with UTF-8 BOM (Excel-friendly)
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(rows)
    
    print(f"✓ Created {OUTPUT_CSV} with proper UTF-8-BOM encoding")
    print("  Hindi text should now display correctly in Excel")
    print(f"  Total rows: {len(rows)}")

if __name__ == "__main__":
    fix_csv_encoding()
