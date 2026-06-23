import os
import sys
import datetime
import pandas as pd

# ============================================================
# CONFIGURATION — change FREQ here to switch between:
#   "W"  = Weekly  (~1,040 rows / 20 years)
#   "M"  = Monthly (~240  rows / 20 years)
# ============================================================
FREQ = "W"

# We start from 2006 to cover 20 years of history
START_DATE = "2006-06-01"
END_DATE   = datetime.date.today().strftime("%Y-%m-%d")

# Output CSV filenames will be suffixed with frequency, e.g.:
#   sox_pe_data_W.csv  /  sox_pe_data_M.csv
INDICES = {
    ".SOX":  "sox_pe_data",
    ".SPX":  "spx_pe_data",
    ".IXIC": "ixic_pe_data",
    ".DJI":  "dji_pe_data",
}


# ---- LSEG Data Library (lseg.data) -------------------------
def fetch_lseg(ticker: str) -> pd.DataFrame:
    print(f"  [LSEG] Opening session for {ticker} ...")
    import lseg.data as ld

    try:
        ld.open_session()
    except Exception as e:
        print(f"  [LSEG] Direct session failed ({e}), trying desktop.workspace ...")
        ld.open_session(name="desktop.workspace")

    print(f"  [LSEG] Querying {ticker} | Frq={FREQ} | {START_DATE} -> {END_DATE}")
    df = ld.get_data(
        universe=[ticker],
        fields=[
            "TR.PriceClose.date",
            "TR.PriceClose",
            "TR.Index_PE_RTRS.date",
            "TR.Index_PE_RTRS",
            "TR.Index_EST_PE_Y1_RTRS.date",
            "TR.Index_EST_PE_Y1_RTRS",
            "TR.Index_EST_PE_Y2_RTRS.date",
            "TR.Index_EST_PE_Y2_RTRS",
        ],
        parameters={"SDate": START_DATE, "EDate": END_DATE, "Frq": FREQ},
    )
    ld.close_session()
    return df


# ---- Eikon API fallback ------------------------------------
def fetch_eikon(ticker: str) -> pd.DataFrame:
    print(f"  [Eikon] Falling back to Eikon API for {ticker} ...")
    import eikon as ek

    app_key = os.environ.get("LSEG_APP_KEY", "dummy_app_key")
    ek.set_app_key(app_key)

    df, err = ek.get_data(
        instruments=[ticker],
        fields=[
            "TR.PriceClose.date",
            "TR.PriceClose",
            "TR.Index_PE_RTRS.date",
            "TR.Index_PE_RTRS",
            "TR.Index_EST_PE_Y1_RTRS.date",
            "TR.Index_EST_PE_Y1_RTRS",
            "TR.Index_EST_PE_Y2_RTRS.date",
            "TR.Index_EST_PE_Y2_RTRS",
        ],
        parameters={"SDate": START_DATE, "EDate": END_DATE, "Frq": FREQ},
    )
    if err:
        print(f"  [Eikon] Warnings: {err}")
    return df


# ---- Merge & save ------------------------------------------
def process_and_save(df: pd.DataFrame, ticker: str, base_name: str) -> str:
    """Align columns, merge on date, calculate Rolling 12M Forward PE, and save."""

    df_price = df.iloc[:, [0, 1, 2]].dropna()
    df_price.columns = ["Instrument", "Date", "Price"]

    df_pe = df.iloc[:, [0, 3, 4]].dropna()
    df_pe.columns = ["Instrument", "Date", "PE"]

    df_y1 = df.iloc[:, [0, 5, 6]].dropna()
    df_y1.columns = ["Instrument", "Date", "Y1_PE"]

    df_y2 = df.iloc[:, [0, 7, 8]].dropna()
    df_y2.columns = ["Instrument", "Date", "Y2_PE"]

    for d in [df_price, df_pe, df_y1, df_y2]:
        d["Date"] = pd.to_datetime(d["Date"]).dt.strftime("%Y-%m-%d")

    merged = pd.merge(df_price, df_pe, on=["Instrument", "Date"], how="inner")
    merged = pd.merge(merged, df_y1, on=["Instrument", "Date"], how="left")
    merged = pd.merge(merged, df_y2, on=["Instrument", "Date"], how="left")

    # Clean scaling issues in estimated P/E (commonly seen in Eikon/LSEG Nasdaq Composite .IXIC estimates)
    for col in ["Y1_PE", "Y2_PE"]:
        # If value is between 0.01 and 0.1, it was divided by 1000
        merged.loc[(merged[col] >= 0.01) & (merged[col] <= 0.1), col] *= 1000.0
        # If value is between 0.0001 and 0.01, it was divided by Index Price
        merged.loc[(merged[col] >= 0.0001) & (merged[col] < 0.01), col] *= merged["Price"]

    # Calculate Rolling 12M Forward PE using day of year weight
    date_dt = pd.to_datetime(merged["Date"])
    day_of_year = date_dt.dt.dayofyear
    # Handle leap year
    days_in_year = date_dt.apply(lambda x: 366 if x.is_leap_year else 365)
    weight_y2 = day_of_year / days_in_year
    weight_y1 = 1.0 - weight_y2

    merged["Forward_PE"] = weight_y1 * merged["Y1_PE"] + weight_y2 * merged["Y2_PE"]
    
    # Fallback to Y1_PE if Y2_PE is missing
    merged["Forward_PE"] = merged["Forward_PE"].fillna(merged["Y1_PE"])

    # We can also keep Y1_PE and Y2_PE in the CSV for transparency
    merged = merged.sort_values("Date").reset_index(drop=True)

    out_file = f"{base_name}_{FREQ}.csv"
    merged.to_csv(out_file, index=False)
    return out_file


def main():
    print(f"Running query for indices: {list(INDICES.keys())}")
    for ticker, base_name in INDICES.items():
        print(f"\nQuerying {ticker}...")
        df = None
        try:
            df = fetch_lseg(ticker)
        except Exception as e:
            print(f"LSEG fetch failed for {ticker}: {e}. Trying Eikon fallback...")
            try:
                df = fetch_eikon(ticker)
            except Exception as e2:
                print(f"Eikon fallback also failed: {e2}")
                continue
        
        if df is not None and not df.empty:
            out_file = process_and_save(df, ticker, base_name)
            print(f"Successfully saved merged data to {out_file}")
        else:
            print(f"No data retrieved for {ticker}")

if __name__ == "__main__":
    main()