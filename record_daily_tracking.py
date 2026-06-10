import os
import sys
import json
import urllib.request
import datetime
import pandas as pd
import yfinance as yf

# SOX (Philadelphia Semiconductor Index) - 30 components
SOX_COMPONENTS = [
    'NVDA', 'AVGO', 'AMD',  'QCOM', 'AMAT',
    'LRCX', 'KLAC', 'MU',   'TXN',  'ADI',
    'MCHP', 'ON',   'MRVL', 'NXPI', 'MPWR',
    'SWKS', 'QRVO', 'TER',  'ENTG', 'STM',
    'ASML', 'INTC', 'MKSI', 'WOLF', 'ACLS',
    'CAMT', 'FORM', 'SITM', 'RMBS', 'COHU'
]

CSV_FILE = "sox_daily_tracking_log.csv"

# Other indices to track with Rolling 12M Forward PE (simple LSEG-only log)
OTHER_INDICES = [
    {"ticker": ".SPX",  "name": "SPX",  "csv": "spx_daily_tracking_log.csv"},
    {"ticker": ".IXIC", "name": "IXIC", "csv": "ixic_daily_tracking_log.csv"},
    {"ticker": ".DJI",  "name": "DJI",  "csv": "dji_daily_tracking_log.csv"},
]

def fetch_lseg_data():
    """Fetch latest price, PE, and Forward PE for .SOX index from LSEG Workspace."""
    print("[LSEG] Attempting to connect via LSEG Data Library...")
    import lseg.data as ld
    
    opened = False
    try:
        ld.open_session()
        opened = True
        print("[LSEG] Session opened successfully.")
    except Exception as e:
        print(f"[LSEG] Direct session failed: {e}. Trying desktop.workspace...")
        try:
            ld.open_session(name="desktop.workspace")
            opened = True
            print("[LSEG] Desktop workspace session opened.")
        except Exception as e2:
            print(f"[LSEG] Session open failed: {e2}")
            
    if not opened:
        # Fallback to Eikon
        print("[LSEG] Attempting fallback to Eikon Data API...")
        try:
            import eikon as ek
            app_key = os.environ.get("LSEG_APP_KEY", "dummy_app_key")
            ek.set_app_key(app_key)
            df, err = ek.get_data(
                instruments=[".SOX"],
                fields=["TR.PriceClose", "TR.Index_PE_RTRS", "TR.Index_EST_PE_Y1_RTRS", "TR.Index_EST_PE_Y2_RTRS"]
            )
            if err:
                print(f"[Eikon] API warning: {err}")
            if df is not None and not df.empty:
                # Rename columns explicitly by position
                df.columns = ['Instrument', 'Price Close', 'Calculated PE Ratio', 'Y1 PE Ratio', 'Y2 PE Ratio']
                return df
        except Exception as e3:
            print(f"[Eikon] Fallback failed: {e3}")
            return None
            
    try:
        df = ld.get_data(
            universe=[".SOX"],
            fields=["TR.PriceClose", "TR.Index_PE_RTRS", "TR.Index_EST_PE_Y1_RTRS", "TR.Index_EST_PE_Y2_RTRS"]
        )
        ld.close_session()
        if df is not None and not df.empty:
            df.columns = ['Instrument', 'Price Close', 'Calculated PE Ratio', 'Y1 PE Ratio', 'Y2 PE Ratio']
        return df
    except Exception as e:
        print(f"[LSEG] Query failed: {e}")
        try:
            ld.close_session()
        except:
            pass
        return None


def fetch_yfinance_bottomup():
    """Fetch prices and EPS for SOX 30 components from yfinance and compute bottom-up PE."""
    print("[yfinance] Fetching data for 30 component stocks...")
    
    rows = []
    missing_fwd = []
    missing_trail = []
    
    for tkr in SOX_COMPONENTS:
        try:
            info = yf.Ticker(tkr).info
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            fwd_eps = info.get('forwardEps')
            trail_eps = info.get('trailingEps')
            
            rows.append({
                'Ticker': tkr,
                'Price': price,
                'Trail_EPS': trail_eps,
                'Fwd_EPS': fwd_eps
            })
            
            if fwd_eps is None:
                missing_fwd.append(tkr)
            if trail_eps is None:
                missing_trail.append(tkr)
        except Exception as e:
            print(f"[yfinance] Error fetching {tkr}: {e}")
            missing_fwd.append(tkr)
            missing_trail.append(tkr)
            
    df = pd.DataFrame(rows).dropna(subset=['Price'])
    if df.empty:
        print("[yfinance] Error: Could not fetch data for any components.")
        return None, None, [], []
        
    # Trailing PE
    df_trail = df.dropna(subset=['Trail_EPS'])
    if not df_trail.empty:
        yf_trail_pe = df_trail['Price'].sum() / df_trail['Trail_EPS'].sum()
    else:
        yf_trail_pe = None
        
    # Forward PE
    df_fwd = df.dropna(subset=['Fwd_EPS'])
    if not df_fwd.empty:
        yf_fwd_pe = df_fwd['Price'].sum() / df_fwd['Fwd_EPS'].sum()
    else:
        yf_fwd_pe = None
        
    return yf_trail_pe, yf_fwd_pe, missing_trail, missing_fwd


def fetch_invesco_api():
    """Fetch latest fund characteristics from Invesco SOXQ API."""
    print("[Invesco] Fetching SOXQ ETF stats via cache API...")
    url = 'https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/46138G615?expand=nav&idType=cusip&variationType=fundCharacteristics&productType=ETF'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        effective_date = data.get("effectiveDate")
        invesco_pe = data.get("priceToEarningsRatio")
        invesco_fwd_pe = data.get("forwardPriceToEarningsRatio")
        
        print(f"[Invesco] API Success. Effective Date: {effective_date}")
        return effective_date, invesco_pe, invesco_fwd_pe
    except Exception as e:
        print(f"[Invesco] Error fetching from API: {e}")
        return None, None, None


def main():
    run_date = datetime.date.today().strftime('%Y-%m-%d')
    today = datetime.date.today()
    print("=" * 70)
    print(f"  SOX Index Daily PE Tracking Log - Run Date: {run_date}")
    print("=" * 70)
    
    # 1. Fetch LSEG
    lseg_price, lseg_pe, lseg_fwd_pe = None, None, None
    try:
        df_lseg = fetch_lseg_data()
        if df_lseg is not None and not df_lseg.empty:
            lseg_price = float(df_lseg['Price Close'].iloc[0])
            lseg_pe = float(df_lseg['Calculated PE Ratio'].iloc[0])
            
            y1_pe = float(df_lseg['Y1 PE Ratio'].iloc[0])
            y2_pe_val = df_lseg['Y2 PE Ratio'].iloc[0]
            if pd.notna(y2_pe_val):
                y2_pe = float(y2_pe_val)
                day_of_year = today.timetuple().tm_yday
                is_leap = (today.year % 4 == 0 and (today.year % 100 != 0 or today.year % 400 == 0))
                days_in_year = 366 if is_leap else 365
                weight_y2 = day_of_year / days_in_year
                weight_y1 = 1.0 - weight_y2
                lseg_fwd_pe = weight_y1 * y1_pe + weight_y2 * y2_pe
            else:
                lseg_fwd_pe = y1_pe
            
            print(f"[LSEG] Close={lseg_price:.2f}, PE={lseg_pe:.2f}x, FwdPE={lseg_fwd_pe:.2f}x (Rolling 12M)")
        else:
            print("[LSEG] Warning: No LSEG data retrieved. Logging as N/A.")
    except Exception as e:
        print(f"[LSEG] Error processing LSEG data: {e}. Logging as N/A.")
        
    # 2. Fetch yfinance
    yf_pe, yf_fwd_pe = None, None
    missing_t, missing_f = [], []
    try:
        yf_pe, yf_fwd_pe, missing_t, missing_f = fetch_yfinance_bottomup()
        if yf_pe is not None:
            print(f"[yfinance] Calculated PE={yf_pe:.2f}x, FwdPE={yf_fwd_pe:.2f}x")
        else:
            print("[yfinance] Warning: No yfinance PE calculated.")
    except Exception as e:
        print(f"[yfinance] Error during calculations: {e}")
        
    # 3. Fetch Invesco SOXQ
    inv_date, inv_pe, inv_fwd_pe = fetch_invesco_api()
    if inv_pe is not None:
        print(f"[Invesco] SOXQ PE={inv_pe:.2f}x, FwdPE={inv_fwd_pe:.2f}x (as of {inv_date})")
        
    # 4. Calculate metrics
    diff_pe_yf = (lseg_pe - yf_pe) if (lseg_pe is not None and yf_pe is not None) else None
    diff_fwd_pe_yf = (lseg_fwd_pe - yf_fwd_pe) if (lseg_fwd_pe is not None and yf_fwd_pe is not None) else None
    ratio_pe_yf = (lseg_pe / yf_pe) if (lseg_pe is not None and yf_pe is not None and yf_pe != 0) else None
    ratio_fwd_pe_yf = (lseg_fwd_pe / yf_fwd_pe) if (lseg_fwd_pe is not None and yf_fwd_pe is not None and yf_fwd_pe != 0) else None
    
    diff_pe_inv = (lseg_pe - inv_pe) if (lseg_pe is not None and inv_pe is not None) else None
    diff_fwd_pe_inv = (lseg_fwd_pe - inv_fwd_pe) if (lseg_fwd_pe is not None and inv_fwd_pe is not None) else None
    
    # 5. Append or Update in CSV
    new_data = {
        'Date': run_date,
        'LSEG_Price': lseg_price,
        'LSEG_PE': lseg_pe,
        'LSEG_FwdPE': lseg_fwd_pe,
        'YF_PE': yf_pe,
        'YF_FwdPE': yf_fwd_pe,
        'Invesco_AsOfDate': inv_date,
        'Invesco_PE': inv_pe,
        'Invesco_FwdPE': inv_fwd_pe,
        'Diff_PE_YF': diff_pe_yf,
        'Diff_FwdPE_YF': diff_fwd_pe_yf,
        'Ratio_PE_YF': ratio_pe_yf,
        'Ratio_FwdPE_YF': ratio_fwd_pe_yf,
        'Diff_PE_Invesco': diff_pe_inv,
        'Diff_FwdPE_Invesco': diff_fwd_pe_inv,
        'Missing_YF_Trail_Count': len(missing_t),
        'Missing_YF_Fwd_Count': len(missing_f),
        'Last_Updated_Time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if os.path.exists(CSV_FILE):
        print(f"\n[CSV] Loading existing log file: {CSV_FILE}")
        df_log = pd.read_csv(CSV_FILE)
        # Check if row for today already exists
        if run_date in df_log['Date'].values:
            print(f"[CSV] Row for {run_date} already exists. Overwriting with new values.")
            idx = df_log[df_log['Date'] == run_date].index[0]
            for col, val in new_data.items():
                df_log.at[idx, col] = val
        else:
            print(f"[CSV] Appending new row for {run_date}.")
            df_new_row = pd.DataFrame([new_data])
            df_log = pd.concat([df_log, df_new_row], ignore_index=True)
    else:
        print(f"\n[CSV] Creating new log file: {CSV_FILE}")
        df_log = pd.DataFrame([new_data])
        
    df_log.to_csv(CSV_FILE, index=False)
    print(f"[CSV] Successfully saved log file to {os.path.abspath(CSV_FILE)}")
    
    # 6. Display comparison table
    print("\n" + "=" * 70)
    print("  SUMMARY COMPARISON TABLE")
    print("=" * 70)
    print(f"{'Source':<15} | {'Trailing PE':>12} | {'Forward PE':>12} | {'As-of Date':>12}")
    print("-" * 70)
    
    lseg_pe_str = f"{lseg_pe:.2f}x" if lseg_pe is not None else "N/A"
    lseg_fwd_str = f"{lseg_fwd_pe:.2f}x" if lseg_fwd_pe is not None else "N/A"
    print(f"{'LSEG Index':<15} | {lseg_pe_str:>12} | {lseg_fwd_str:>12} | {run_date:>12}")
    
    yf_pe_str = f"{yf_pe:.2f}x" if yf_pe is not None else "N/A"
    yf_fwd_str = f"{yf_fwd_pe:.2f}x" if yf_fwd_pe is not None else "N/A"
    print(f"{'yfinance (BU)':<15} | {yf_pe_str:>12} | {yf_fwd_str:>12} | {run_date:>12}")
    
    inv_pe_str = f"{inv_pe:.2f}x" if inv_pe is not None else "N/A"
    inv_fwd_str = f"{inv_fwd_pe:.2f}x" if inv_fwd_pe is not None else "N/A"
    inv_date_str = inv_date if inv_date is not None else "N/A"
    print(f"{'Invesco SOXQ':<15} | {inv_pe_str:>12} | {inv_fwd_str:>12} | {inv_date_str:>12}")
    
    print("-" * 70)
    ratio_pe_str = f"{ratio_pe_yf:.3f}" if ratio_pe_yf is not None else "N/A"
    ratio_fwd_str = f"{ratio_fwd_pe_yf:.3f}" if ratio_fwd_pe_yf is not None else "N/A"
    print(f"{'Ratio (LSEG/YF)':<15} | {ratio_pe_str:>12} | {ratio_fwd_str:>12} | {'-':>12}")
    
    diff_pe_str = f"{diff_pe_yf:+.2f}x" if diff_pe_yf is not None else "N/A"
    diff_fwd_str = f"{diff_fwd_pe_yf:+.2f}x" if diff_fwd_pe_yf is not None else "N/A"
    print(f"{'Diff (LSEG-YF)':<15} | {diff_pe_str:>12} | {diff_fwd_str:>12} | {'-':>12}")
    print("=" * 70)
    
    if len(missing_t) > 0 or len(missing_f) > 0:
        print(f"Note: yfinance had missing data. Trail missing: {len(missing_t)}, Fwd missing: {len(missing_f)}")
    print("Log process completed successfully.\n")

if __name__ == "__main__":
    main()