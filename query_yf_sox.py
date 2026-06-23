import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import os

# SOX (Philadelphia Semiconductor Index) - 30 components
SOX_COMPONENTS = [
    'NVDA', 'AVGO', 'AMD',  'QCOM', 'AMAT',
    'LRCX', 'KLAC', 'MU',   'TXN',  'ADI',
    'MCHP', 'ON',   'MRVL', 'NXPI', 'MPWR',
    'SWKS', 'QRVO', 'TER',  'ENTG', 'STM',
    'ASML', 'INTC', 'MKSI', 'WOLF', 'ACLS',
    'CAMT', 'FORM', 'SITM', 'RMBS', 'COHU'
]

def main():
    print("======================================================================")
    # 1. Fetch weekly historical prices for all components (last 5 years)
    print("[yfinance] Fetching weekly price history for 30 components...")
    start_date = (datetime.date.today() - datetime.timedelta(days=5*365)).strftime('%Y-%m-%d')
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    
    price_df = yf.download(SOX_COMPONENTS, start=start_date, end=end_date, interval="1wk")
    if 'Close' in price_df.columns:
        price_df = price_df['Close']
    
    # Fill missing prices
    price_df = price_df.ffill().bfill()
    price_df.index = pd.to_datetime(price_df.index).tz_localize(None)
    
    # 2. Fetch earnings dates for all components
    print("[yfinance] Fetching earnings dates & EPS history for 30 components...")
    eps_history = {}
    for i, tkr in enumerate(SOX_COMPONENTS):
        print(f"  [{i+1}/30] Fetching {tkr} ...")
        try:
            t = yf.Ticker(tkr)
            df_earnings = t.earnings_dates
            if df_earnings is not None and not df_earnings.empty:
                # Reset index to get Earnings Date as a column
                df_earnings = df_earnings.reset_index()
                # Parse date and normalize timezone
                df_earnings['Earnings Date'] = pd.to_datetime(df_earnings['Earnings Date']).dt.tz_localize(None)
                # Sort ascending
                df_earnings = df_earnings.sort_values('Earnings Date').reset_index(drop=True)
                eps_history[tkr] = df_earnings
            else:
                print(f"  ⚠️ No earnings dates for {tkr}")
        except Exception as e:
            print(f"  ❌ Error fetching {tkr}: {e}")
            
    # 3. Calculate weekly bottom-up PE
    print("\n[yfinance] Calculating weekly bottom-up P/E history...")
    results = []
    
    for date in price_df.index:
        sum_price = 0.0
        sum_trail_eps = 0.0
        sum_fwd_eps = 0.0
        
        valid_trail_stocks = 0
        valid_fwd_stocks = 0
        
        for tkr in SOX_COMPONENTS:
            if tkr not in eps_history or tkr not in price_df.columns:
                continue
                
            price = price_df.loc[date, tkr]
            if pd.isna(price) or price <= 0:
                continue
                
            sum_price += price
            
            df_e = eps_history[tkr]
            
            # Trailing EPS: sum of Reported EPS of the last 4 earnings releases before 'date'
            past_releases = df_e[df_e['Earnings Date'] <= date].tail(4)
            if len(past_releases) == 4 and past_releases['Reported EPS'].notna().all():
                trail_eps = past_releases['Reported EPS'].sum()
                sum_trail_eps += trail_eps
                valid_trail_stocks += 1
                
            # Forward EPS: sum of EPS Estimate of the next 4 earnings releases after/on 'date'
            fwd_releases = df_e[df_e['Earnings Date'] > date].head(4)
            if len(fwd_releases) == 4 and fwd_releases['EPS Estimate'].notna().all():
                fwd_eps = fwd_releases['EPS Estimate'].sum()
                sum_fwd_eps += fwd_eps
                valid_fwd_stocks += 1
                
        # Only output if we have sufficient stock data (e.g. at least 25 out of 30 stocks)
        if valid_trail_stocks >= 25 and valid_fwd_stocks >= 25:
            pe_trail = sum_price / sum_trail_eps if sum_trail_eps > 0 else np.nan
            pe_fwd = sum_price / sum_fwd_eps if sum_fwd_eps > 0 else np.nan
            
            results.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Price': sum_price,  # Sum of component prices (as index price proxy)
                'PE': pe_trail,
                'Forward_PE': pe_fwd
            })
            
    df_out = pd.DataFrame(results).dropna()
    df_out = df_out.sort_values('Date').reset_index(drop=True)
    
    # 4. Save to CSV
    out_file = "sox_yf_pe_data_W.csv"
    df_out.to_csv(out_file, index=False)
    print(f"\n[yfinance] Successfully saved {len(df_out)} rows to {out_file}")
    print(df_out.tail(10))

if __name__ == "__main__":
    main()
