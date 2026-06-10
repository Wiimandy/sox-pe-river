import os
import shutil
import datetime

# Source files directory (scratch directory where plot_river.py runs)
src_dir = r"C:\Users\User\.gemini\antigravity\scratch\sox-pe-river"

# Target directory
dest_dir = r"C:\Users\User\OneDrive\NoWorkLook\Week\Week Charts"

# Get current date in YYMMDD format
yymmdd = datetime.datetime.now().strftime("%y%m%d")
print(f"Current Date Code (yymmdd): {yymmdd}")

# Define the source to target filename mappings
# We only use index ticker abbreviations (SOX, SPX, IXIC, DJI)
mappings = {
    "sox_pe_fwd_trend.png": [
        f"SOX PER_{yymmdd}.png"
    ],
    "spx_pe_fwd_trend.png": [
        f"SPX PER_{yymmdd}.png"
    ],
    "ixic_pe_fwd_trend.png": [
        f"IXIC PER_{yymmdd}.png"
    ],
    "dji_pe_fwd_trend.png": [
        f"DJI PER_{yymmdd}.png"
    ]
}

# List of full names to clean up from target folder
to_cleanup = [
    f"S&P 500 PER_{yymmdd}.png",
    f"NASDAQ PER_{yymmdd}.png",
    f"Dow Jones PER_{yymmdd}.png"
]

# Create target directory if it doesn't exist
if not os.path.exists(dest_dir):
    try:
        os.makedirs(dest_dir)
        print(f"Created destination directory: {dest_dir}")
    except Exception as e:
        print(f"Error creating directory: {e}")
        exit(1)

print("\nCopying and renaming charts...")
print("-" * 50)

for src_name, dest_names in mappings.items():
    src_path = os.path.join(src_dir, src_name)
    if not os.path.exists(src_path):
        print(f"⚠️ Source file not found: {src_path}")
        continue
        
    for dest_name in dest_names:
        dest_path = os.path.join(dest_dir, dest_name)
        try:
            shutil.copy2(src_path, dest_path)
            print(f"  OK     Copied: {src_name} -> {dest_name}")
        except Exception as e:
            print(f"  ERROR  Error copying to {dest_name}: {e}")

print("-" * 50)
print("\nCleaning up full-name legacy files...")
for name in to_cleanup:
    cleanup_path = os.path.join(dest_dir, name)
    if os.path.exists(cleanup_path):
        try:
            os.remove(cleanup_path)
            print(f"  CLEAN  Deleted legacy file: {name}")
        except Exception as e:
            print(f"  WARN   Failed to delete {name}: {e}")

print("-" * 50)
print(f"Export completed! All files are in {dest_dir}\n")

