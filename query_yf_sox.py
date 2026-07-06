import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import urllib.request
import json
import os
import calendar

def fetch_cathay_weights():
    print("[Cathay API] Fetching current index weights for 00830 (FundCode=BO)...")
    url = "https://cwapi.cathaysite.com.tw/api/ETF/GetIndexStockWeights?FundCode=BO&status=1"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.cathaysite.com.tw/'
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            content = response.read().decode('utf-8')
        data = json.loads(content)
        if not data.get('success'):
            raise ValueError(f"API returned failure: {data.get('returnMessage')}")
        
        stock_weights = data.get('result', {}).get('stockWeights', [])
        weights = {}
        for sw in stock_weights:
            ticker = sw['stockCode'].replace('.US', '')
            weight = float(sw['weights']) / 100.0
            weights[ticker] = weight
        print(f"[Cathay API] Successfully fetched {len(weights)} components and weights.")
        return weights
    except Exception as e:
        print(f"[Cathay API] Error fetching weights: {e}")
        raise e

def main():
    print("======================================================================")
    print("  SOX Index yfinance Bottom-Up Weighted PE Calculation")
    print("======================================================================")
    
    # 1. Fetch current weights and components from Cathay API
    try:
        weights = fetch_cathay_weights()
    except Exception as e:
        print(f"❌ Failed to fetch weights from Cathay API: {e}. Exiting.")
        return
        
    tickers = list(weights.keys())
    
    # 2. Fetch weekly historical prices for all components + ^SOX (last 5 years)
    print("\n[yfinance] Fetching weekly price history for 30 components + ^SOX...")
    start_date = (datetime.date.today() - datetime.timedelta(days=5*365)).strftime('%Y-%m-%d')
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    
    all_tickers = tickers + ['^SOX']
    price_df = yf.download(all_tickers, start=start_date, end=end_date, interval="1wk")
    if 'Close' in price_df.columns:
        price_df = price_df['Close']
    
    # Fill missing prices
    price_df = price_df.ffill().bfill()
    price_df.index = pd.to_datetime(price_df.index).tz_localize(None)
    
    # Check if ^SOX is present
    if '^SOX' not in price_df.columns:
        print("❌ Error: ^SOX index price is missing in downloaded data.")
        return
        
    # 3. Fetch earnings dates for all components
    print("\n[yfinance] Fetching earnings dates & EPS history for all components...")
    eps_history = {}
    annual_estimates = {}
    for i, tkr in enumerate(tickers):
        print(f"  [{i+1}/{len(tickers)}] Fetching {tkr} ...")
        try:
            t = yf.Ticker(tkr)
            estimates = t.earnings_estimate
            if estimates is not None and not estimates.empty and {'0y', '+1y'}.issubset(estimates.index):
                eps_0y = estimates.loc['0y', 'avg']
                eps_1y = estimates.loc['+1y', 'avg']
                if pd.notna(eps_0y) and pd.notna(eps_1y):
                    annual_estimates[tkr] = (float(eps_0y), float(eps_1y))

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
            
    # 4. Calculate weekly bottom-up weighted PE
    print("\n[yfinance] Calculating weekly bottom-up weighted P/E history...")
    results = []
    
    for date in price_df.index:
        p_index = price_df.loc[date, '^SOX']
        if pd.isna(p_index) or p_index <= 0:
            continue
            
        # Trailing variables
        sum_trail_yield = 0.0
        sum_trail_weight = 0.0
        
        # Forward variables
        sum_fwd_yield = 0.0
        sum_fwd_weight = 0.0
        
        for tkr in tickers:
            if tkr not in price_df.columns:
                continue
                
            price = price_df.loc[date, tkr]
            if pd.isna(price) or price <= 0:
                continue
                
            weight = weights[tkr]
            df_e = eps_history.get(tkr)
            
            # Trailing EPS: sum of Reported EPS of the last 4 earnings releases before 'date'
            past_releases = df_e[df_e['Earnings Date'] <= date].tail(4) if df_e is not None else pd.DataFrame()
            if len(past_releases) == 4 and past_releases['Reported EPS'].notna().all():
                trail_eps = past_releases['Reported EPS'].sum()
                if price > 0:
                    sum_trail_yield += weight * (trail_eps / price)
                    sum_trail_weight += weight
                
            # Forward EPS: sum of EPS Estimate of the next 4 earnings releases after/on 'date'
            fwd_releases = df_e[df_e['Earnings Date'] > date].head(4) if df_e is not None else pd.DataFrame()
            if len(fwd_releases) == 4 and fwd_releases['EPS Estimate'].notna().all():
                fwd_eps = fwd_releases['EPS Estimate'].sum()
                if price > 0:
                    sum_fwd_yield += weight * (fwd_eps / price)
                    sum_fwd_weight += weight
            elif tkr in annual_estimates:
                eps_0y, eps_1y = annual_estimates[tkr]
                days_in_year = 366 if calendar.isleap(date.year) else 365
                year_progress = (date.dayofyear - 1) / days_in_year
                fwd_eps = eps_0y * (1 - year_progress) + eps_1y * year_progress
                if fwd_eps > 0 and price > 0:
                    sum_fwd_yield += weight * (fwd_eps / price)
                    sum_fwd_weight += weight
                    
        # Only output if we have sufficient active weight (at least 70% of total index weight)
        pe_trail = np.nan
        pe_fwd = np.nan
        
        if sum_trail_weight >= 0.70:
            # Re-normalize yield for active weight
            norm_trail_yield = sum_trail_yield / sum_trail_weight
            pe_trail = 1.0 / norm_trail_yield if norm_trail_yield > 0 else np.nan
            
        if sum_fwd_weight >= 0.70:
            # Re-normalize yield for active weight
            norm_fwd_yield = sum_fwd_yield / sum_fwd_weight
            pe_fwd = 1.0 / norm_fwd_yield if norm_fwd_yield > 0 else np.nan
            
        if not pd.isna(pe_trail) or not pd.isna(pe_fwd):
            results.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Price': p_index,  # Actual ^SOX index price close
                'PE': pe_trail,
                'Forward_PE': pe_fwd
            })
            
    df_out = pd.DataFrame(results).dropna(subset=['PE'])
    df_out = df_out.sort_values('Date').reset_index(drop=True)
    
    # 5. Save to CSV
    out_file = "sox_yf_pe_data_W.csv"
    df_out.to_csv(out_file, index=False)
    print(f"\n[yfinance] Successfully saved {len(df_out)} rows to {out_file}")
    print(df_out.tail(10))

if __name__ == "__main__":
    main()
