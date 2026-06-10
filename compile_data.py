import pandas as pd
import json

# ============================================================
# CONFIGURATION — must match query_all.py and plot_river.py
#   "W"  = Weekly
#   "M"  = Monthly
# ============================================================
FREQ = "W"


def main():
    freq_label = "週頻 (Weekly)" if FREQ == "W" else "月頻 (Monthly)"
    print(f"Compiling datasets to data.js  |  Frq = {FREQ}  ({freq_label}) ...")

    datasets = {
        "SOX_DATA":  f"sox_pe_river_data_{FREQ}.csv",
        "SPX_DATA":  f"spx_pe_river_data_{FREQ}.csv",
        "IXIC_DATA": f"ixic_pe_river_data_{FREQ}.csv",
        "DJI_DATA":  f"dji_pe_river_data_{FREQ}.csv",
    }

    with open("data.js", "w", encoding="utf-8") as f:
        for var_name, csv_file in datasets.items():
            df = pd.read_csv(csv_file)
            records = df.to_dict(orient="records")
            f.write(f"const {var_name} = ")
            f.write(json.dumps(records, indent=2))
            f.write(";\n\n")
            print(f"  {var_name:<12} ← {csv_file}  ({len(records)} rows)")

    print(f"\nSuccessfully compiled all 4 datasets into data.js!")
    print(f"(Frequency: {FREQ} — {freq_label})")


if __name__ == "__main__":
    main()
