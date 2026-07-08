import pandas as pd


CUTOFF_DATE = pd.Timestamp("2026-07-06")
SOX_WEEKLY_FILE = "sox_pe_data_W.csv"
TRACKING_FILE = "sox_daily_tracking_log.csv"


def main():
    sox = pd.read_csv(SOX_WEEKLY_FILE)
    sox["Date"] = pd.to_datetime(sox["Date"], errors="coerce", format="mixed")

    lseg = sox[sox["Date"] <= CUTOFF_DATE].copy()

    tracking = pd.read_csv(TRACKING_FILE)
    tracking["Date"] = pd.to_datetime(tracking["Date"], errors="coerce", format="mixed")
    tracking = tracking[tracking["Date"] > CUTOFF_DATE].copy()
    tracking = tracking.dropna(subset=["Date", "YF_PE", "YF_FwdPE"])

    if tracking.empty:
        out = lseg
        print("[splice] No yfinance proxy rows after 2026-07-06 yet. Kept LSEG history only.")
    else:
        tracking = tracking.sort_values("Date")
        tracking = tracking.groupby(pd.Grouper(key="Date", freq="W-FRI")).tail(1)

        if "YF_Index_Price" in tracking.columns:
            price = tracking["YF_Index_Price"]
        else:
            price = tracking["LSEG_Price"]

        yf_proxy = pd.DataFrame({
            "Instrument": ".SOX",
            "Date": tracking["Date"],
            "Price": price,
            "PE": tracking["YF_PE"],
            "Y1_PE": pd.NA,
            "Y2_PE": pd.NA,
            "Forward_PE": tracking["YF_FwdPE"],
            "Source": "YFINANCE_PROXY",
        })
        yf_proxy = yf_proxy.dropna(subset=["Price", "PE", "Forward_PE"])
        out = pd.concat([lseg, yf_proxy], ignore_index=True)
        print(f"[splice] Appended {len(yf_proxy)} yfinance proxy weekly rows after 2026-07-06.")

    out = out.sort_values("Date").drop_duplicates(subset=["Date"], keep="last")
    out["Date"] = out["Date"].dt.strftime("%Y-%m-%d")
    out.to_csv(SOX_WEEKLY_FILE, index=False)
    print(f"[splice] Wrote {len(out)} rows to {SOX_WEEKLY_FILE}.")


if __name__ == "__main__":
    main()
