import os
import sys
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties

# ==============================================================================
# CONFIGURATION
# ==============================================================================
# Target directory for OneDrive Week Charts
OUTPUT_DIR = r"C:\Users\User\OneDrive\NoWorkLook\Week\Week Charts"

# Analysis settings
START_DATE = "2006-06-01"
END_DATE = datetime.date.today().strftime('%Y-%m-%d')
FREQ = "W"  # "W" = Weekly, "M" = Monthly

# Index configurations: LSEG Ticker, output abbreviation, min PE filter value, and custom CJK footnotes
INDICES = [
    {
        "ticker": ".SPX",
        "name": "SPX",
        "min_pe": 12.0,
        "footnote": None
    },
    {
        "ticker": ".DJI",
        "name": "DJI",
        "min_pe": 12.0,
        "footnote": None
    },
    {
        "ticker": ".IXIC",
        "name": "IXIC",
        "min_pe": 21.0,
        "footnote": (
            "※ 數據修正說明｜LSEG 資料庫於 2024 年 1 月至 2025 年 6 月間，多次回傳 Nasdaq Composite 本益比異常低值（最低達 8～14 倍），"
            "與市場實況（正常應在 25～35 倍）嚴重背離，為資料庫計算錯誤所致。本圖採「絕對下限過濾（min P/E = 21x）」剔除異常值後，"
            "以線性插補（Linear Interpolation）進行平滑填補。插補區間內之數值為估算值，非實際觀測數據。"
        )
    },
    {
        "ticker": ".SOX",
        "name": "SOX",
        "min_pe": 12.0,
        "footnote": None
    }
]

# Color palettes corresponding to each index (imitating user YTD reference charts)
INDEX_TREND_COLORS = {
    "SOX": {
        "primary": "#0f5132",  # Deep forest green
        "mean": "#198754",     # Medium green
        "sd_1": "#14b8a6",     # Teal
        "sd_2": "#a7f3d0"      # Pale green
    },
    "SPX": {
        "primary": "#000000",  # Black
        "mean": "#495057",     # Dark grey
        "sd_1": "#6c757d",     # Medium grey
        "sd_2": "#cbd5e1"      # Light grey
    },
    "IXIC": {
        "primary": "#0f2d59",  # Deep navy blue
        "mean": "#0d6efd",     # Royal blue
        "sd_1": "#60a5fa",     # Light blue
        "sd_2": "#bfdbfe"      # Pale blue
    },
    "DJI": {
        "primary": "#7c2d12",  # Dark rust brown
        "mean": "#b45309",     # Terracotta
        "sd_1": "#f59e0b",     # Amber
        "sd_2": "#fde047"      # Sand yellow
    }
}

# CJK-capable font for footnotes (Traditional Chinese on Windows)
CJK_FONT = FontProperties(family='Microsoft JhengHei', size=7)

# ==============================================================================
# DATA INGESTION & FALLBACKS
# ==============================================================================
def fetch_lseg_data(ticker, start_date, end_date, freq):
    """Fetch price and Forward PE series from LSEG Data Library."""
    import lseg.data as ld
    
    # Try opening LSEG workspace session
    opened = False
    try:
        ld.open_session()
        opened = True
    except Exception as e:
        print(f"    [LSEG] Direct session failed: {e}. Trying desktop.workspace...")
        try:
            ld.open_session(name="desktop.workspace")
            opened = True
        except Exception as e2:
            print(f"    [LSEG] Desktop workspace session failed: {e2}")
            
    if not opened:
        raise ConnectionError("LSEG Workspace Data Library session could not be established.")
        
    try:
        print(f"    [LSEG] Querying {ticker} (Rolling 12M Forward PE)...")
        df = ld.get_data(
            universe=[ticker],
            fields=[
                "TR.PriceClose.date",
                "TR.PriceClose",
                "TR.Index_EST_PE_Y1_RTRS.date",
                "TR.Index_EST_PE_Y1_RTRS",
                "TR.Index_EST_PE_Y2_RTRS.date",
                "TR.Index_EST_PE_Y2_RTRS",
            ],
            parameters={"SDate": start_date, "EDate": end_date, "Frq": freq},
        )
        ld.close_session()
        return df
    except Exception as e:
        try:
            ld.close_session()
        except:
            pass
        raise e

def fetch_eikon_fallback(ticker, start_date, end_date, freq):
    """Fallback query utilizing the Eikon Data API directly."""
    import eikon as ek
    
    app_key = os.environ.get("LSEG_APP_KEY", "dummy_app_key")
    ek.set_app_key(app_key)
    
    print(f"    [Eikon] Querying {ticker} (Rolling 12M Forward PE)...")
    df, err = ek.get_data(
        instruments=[ticker],
        fields=[
            "TR.PriceClose.date",
            "TR.PriceClose",
            "TR.Index_EST_PE_Y1_RTRS.date",
            "TR.Index_EST_PE_Y1_RTRS",
            "TR.Index_EST_PE_Y2_RTRS.date",
            "TR.Index_EST_PE_Y2_RTRS",
        ],
        parameters={"SDate": start_date, "EDate": end_date, "Frq": freq},
    )
    if err:
        print(f"    [Eikon] Warnings: {err}")
    return df

def align_and_merge_data(df):
    """Splits columns to align Price, Y1 PE, and Y2 PE, calculating Rolling 12M Forward PE."""
    df_price = df.iloc[:, [0, 1, 2]].dropna()
    df_price.columns = ["Instrument", "Date", "Price"]
    
    df_y1 = df.iloc[:, [0, 3, 4]].dropna()
    df_y1.columns = ["Instrument", "Date", "Y1_PE"]
    
    df_y2 = df.iloc[:, [0, 5, 6]].dropna()
    df_y2.columns = ["Instrument", "Date", "Y2_PE"]
    
    for d in [df_price, df_y1, df_y2]:
        d["Date"] = pd.to_datetime(d["Date"]).dt.strftime("%Y-%m-%d")
        
    merged = pd.merge(df_price, df_y1, on=["Instrument", "Date"], how="inner")
    merged = pd.merge(merged, df_y2, on=["Instrument", "Date"], how="left")
    
    # Calculate Rolling 12M Forward PE using day of year weight
    date_dt = pd.to_datetime(merged["Date"])
    day_of_year = date_dt.dt.dayofyear
    days_in_year = date_dt.apply(lambda x: 366 if x.is_leap_year else 365)
    weight_y2 = day_of_year / days_in_year
    weight_y1 = 1.0 - weight_y2
    
    merged["Forward_PE"] = weight_y1 * merged["Y1_PE"] + weight_y2 * merged["Y2_PE"]
    merged["Forward_PE"] = merged["Forward_PE"].fillna(merged["Y1_PE"])
    
    return merged.sort_values("Date").reset_index(drop=True)

# ==============================================================================
# DATA CLEANING LAYER
# ==============================================================================
def clean_pe_series(series, min_val=12.0, max_deviation=0.35):
    """Applies absolute thresholding and linear interpolation to clean database anomalies."""
    s = series.copy()
    # 1. Absolute lower bound check
    s[s < min_val] = np.nan
    s = s.interpolate(method='linear').ffill().bfill()
    
    # 2. Rolling deviation check (sudden drops/spikes)
    rolling_med = s.rolling(window=13, center=True, min_periods=1).median()
    deviations = np.abs(s - rolling_med) / rolling_med
    is_anomaly = deviations > max_deviation
    
    s[is_anomaly] = np.nan
    s = s.interpolate(method='linear').ffill().bfill()
    return s

# ==============================================================================
# PLOTTING CORE
# ==============================================================================
def plot_pe_trend(df, index_name, min_pe, footnote, yymmdd):
    """Calculates 20-year stats and plots 5-year Rolling 12M Forward PE trend with white background and custom colors."""
    # Clean Forward PE column
    df['Forward_PE'] = clean_pe_series(df['Forward_PE'], min_val=min_pe, max_deviation=0.35)
    
    # Calculate 20-year boundaries from full dataset
    mean_fwd_pe = df['Forward_PE'].mean()
    std_fwd_pe = df['Forward_PE'].std()
    
    # Extract colors config
    colors = INDEX_TREND_COLORS.get(index_name, {
        "primary": "black", "mean": "grey", "sd_1": "lightgrey", "sd_2": "lightgrey"
    })
    
    with plt.style.context('default'):
        # Set exact size 1200x500 pixels (12x5 inches at 100 DPI)
        fig, ax = plt.subplots(figsize=(12, 5), dpi=100, facecolor='white')
        ax.set_facecolor('white')
        
        # Filter dataframe to the last 5 years for plotting
        df_plot = df.copy()
        df_plot['Date_dt'] = pd.to_datetime(df_plot['Date'])
        max_date = df_plot['Date_dt'].max()
        cutoff_date = max_date - pd.DateOffset(years=5)
        df_plot = df_plot[df_plot['Date_dt'] >= cutoff_date]
        
        dates = df_plot['Date_dt']
        
        # Plot P/E Trend (last 5 years)
        ax.plot(dates, df_plot['Forward_PE'], color=colors["primary"], linewidth=2.5, label=f'{index_name} Rolling 12M Forward P/E')
        
        # Draw horizontal boundaries (reference boundaries still calculated from 20-year data)
        ax.axhline(mean_fwd_pe, color=colors["mean"], alpha=0.8, linestyle='-', linewidth=2.0, label=f'20-Yr Average ({mean_fwd_pe:.2f}x)')
        ax.axhline(mean_fwd_pe + std_fwd_pe, color=colors["sd_1"], alpha=0.7, linestyle='--', linewidth=1.5, label=f'+1 SD ({(mean_fwd_pe + std_fwd_pe):.2f}x)')
        ax.axhline(mean_fwd_pe - std_fwd_pe, color=colors["sd_1"], alpha=0.7, linestyle='--', linewidth=1.5, label=f'-1 SD ({(mean_fwd_pe - std_fwd_pe):.2f}x)')
        ax.axhline(mean_fwd_pe + 2 * std_fwd_pe, color=colors["sd_2"], alpha=0.6, linestyle='-.', linewidth=1.5, label=f'+2 SD ({(mean_fwd_pe + 2*std_fwd_pe):.2f}x)')
        ax.axhline(mean_fwd_pe - 2 * std_fwd_pe, color=colors["sd_2"], alpha=0.6, linestyle='-.', linewidth=1.5, label=f'-2 SD ({(mean_fwd_pe - 2*std_fwd_pe):.2f}x)')
        
        # Formatting elements
        title_str = f'{index_name} Index Historical Rolling 12M Forward P/E Trend & Valuation Boundaries (5 Years)'
        ax.set_title(title_str, fontsize=15, fontweight='bold', pad=15, color='#1e293b')
        ax.set_xlabel('Year', fontsize=11, labelpad=8, color='#334155')
        ax.set_ylabel('Rolling 12M Forward P/E Ratio', fontsize=11, labelpad=8, color='#334155')
        
        # Ticks and boundaries
        ax.xaxis.set_major_locator(mdates.YearLocator(1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        plt.xticks(rotation=0)
        
        ax.tick_params(colors='#334155', labelsize=10)
        ax.spines['bottom'].set_color('#cbd5e1')
        ax.spines['left'].set_color('#cbd5e1')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        ax.grid(True, which='both', linestyle=':', color='#e2e8f0', alpha=0.8)
        ax.legend(loc='lower left', facecolor='white', edgecolor='#cbd5e1', labelcolor='#334155', framealpha=0.95, ncol=3, fontsize=9)
        
        plt.tight_layout()
        
        if footnote:
            plt.figtext(0.5, -0.04, footnote, ha='center', va='top',
                        fontproperties=CJK_FONT, color='#475569', wrap=True,
                        bbox=dict(boxstyle='round,pad=0.4', facecolor='#f8fafc', edgecolor='#cbd5e1', alpha=0.9))
            plt.subplots_adjust(bottom=0.18)
            
        dest_filename = f"{index_name} PER_{yymmdd}.png"
        dest_path = os.path.join(OUTPUT_DIR, dest_filename)
        
        plt.savefig(dest_path, facecolor='white', edgecolor='none', bbox_inches='tight')
        plt.close()
        print(f"    [Export] Saved: {dest_filename}")

# ==============================================================================
# MAIN PIPELINE
# ==============================================================================
def main():
    print("=" * 70)
    print("  Local Valuation Tool - Rolling 12M Forward PE Trend Chart Generator & Exporter")
    print(f"  Target Folder: {OUTPUT_DIR}")
    print("=" * 70)
    
    # Ensure output folder exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created destination directory: {OUTPUT_DIR}")
        
    yymmdd = datetime.datetime.now().strftime("%y%m%d")
    
    for ind in INDICES:
        ticker = ind["ticker"]
        name = ind["name"]
        min_pe = ind["min_pe"]
        footnote = ind["footnote"]
        
        print(f"\nProcessing Index: {name} ({ticker}) ...")
        df_merged = None
        
        # 1. Fetching raw data
        try:
            df_raw = fetch_lseg_data(ticker, START_DATE, END_DATE, FREQ)
            df_merged = align_and_merge_data(df_raw)
        except Exception as e:
            print(f"    [LSEG] Library failed: {e}. Trying fallback to Eikon Data API...")
            try:
                df_raw = fetch_eikon_fallback(ticker, START_DATE, END_DATE, FREQ)
                df_merged = align_and_merge_data(df_raw)
            except Exception as e2:
                print(f"    [Eikon] Fallback failed: {e2}")
                
                # Try local CSV fallback
                local_csv = f"{name.lower()}_pe_data_{FREQ}.csv"
                local_csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), local_csv)
                if not os.path.exists(local_csv_path):
                    local_csv_path = local_csv
                
                if os.path.exists(local_csv_path):
                    print(f"    [Local Fallback] Attempting to load from local CSV: {local_csv_path}")
                    try:
                        df_merged = pd.read_csv(local_csv_path)
                        # Check columns mapping
                        if 'Forward_PE' not in df_merged.columns and 'Forward PE' in df_merged.columns:
                            df_merged.rename(columns={'Forward PE': 'Forward_PE'}, inplace=True)
                        print(f"    [Local Fallback] Successfully loaded {len(df_merged)} rows.")
                    except Exception as e3:
                        print(f"    [Local Fallback] Error reading CSV: {e3}")
                
                if df_merged is None:
                    print(f"    ⚠️ Skipping {name} - All data acquisition channels failed.")
                    continue
                    
        if df_merged is not None and not df_merged.empty:
            # 3. Plot and save directly
            plot_pe_trend(df_merged, name, min_pe, footnote, yymmdd)
        else:
            print(f"    ⚠️ Empty dataset for {name}.")
            
    # Clean up legacy files
    legacy_files = [
        f"S&P 500 PER_{yymmdd}.png",
        f"NASDAQ PER_{yymmdd}.png",
        f"Dow Jones PER_{yymmdd}.png"
    ]
    print("\nCleaning up legacy files...")
    for leg_file in legacy_files:
        leg_path = os.path.join(OUTPUT_DIR, leg_file)
        if os.path.exists(leg_path):
            try:
                os.remove(leg_path)
                print(f"    [Clean] Removed: {leg_file}")
            except Exception as e:
                print(f"    [Clean] Warning: Failed to remove {leg_file} ({e})")
                
    print("\n" + "=" * 70)
    print("  Pipeline execution completed successfully.")
    print("=" * 70)

if __name__ == "__main__":
    main()