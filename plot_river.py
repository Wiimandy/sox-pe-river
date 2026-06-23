import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties

# ============================================================
# CONFIGURATION — must match query_all.py
#   "W"  = Weekly  (~1,040 rows / 20 years)
#   "M"  = Monthly (~240  rows / 20 years)
# ============================================================
FREQ = "W"

# Set up matplotlib style for a premium dark look
plt.style.use('dark_background')
plt.rcParams['font.sans-serif'] = ['Arial', 'Inter', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# CJK-capable font for footnote text (Traditional Chinese support on Windows)
_CJK_FONT = FontProperties(family='Microsoft JhengHei', size=7)

def clean_pe_series(series, dates=None, index_name=None, min_val=9.5, max_deviation=0.35):
    s = series.copy()
    if index_name == 'IXIC' and dates is not None:
        # Date-based hybrid filtering for Nasdaq index
        dates_dt = pd.to_datetime(dates)
        is_early = dates_dt < '2023-12-01'
        # Early data lower bound is 14.0 (retains historical 17-21 range)
        s[is_early & (s < 14.0)] = np.nan
        # Recent data lower bound is 21.0 (filters out LSEG database errors)
        s[(~is_early) & (s < 21.0)] = np.nan
    else:
        # Standard absolute lower bound
        s[s < min_val] = np.nan
        
    s = s.interpolate(method='linear').ffill().bfill()
    
    # 2. Rolling median deviation filter (detect sudden spikes or drops)
    rolling_med = s.rolling(window=13, center=True, min_periods=1).median()
    deviations = np.abs(s - rolling_med) / rolling_med
    is_anomaly = deviations > max_deviation
    
    s[is_anomaly] = np.nan
    s = s.interpolate(method='linear').ffill().bfill()
    return s

def calculate_river_bands(df, index_name="SOX", fixed_pe_levels=[15, 20, 25, 30, 35, 40], min_val=12.0):
    # Clean PE and Forward_PE columns using robust anomaly filtering with index-specific min_val and dates
    df['PE'] = clean_pe_series(df['PE'], dates=df['Date'], index_name=index_name, min_val=min_val, max_deviation=0.35)
    df['Forward_PE'] = clean_pe_series(df['Forward_PE'], dates=df['Date'], index_name=index_name, min_val=min_val, max_deviation=0.35)
    
    # Implied Trailing EPS = Price / PE
    df['EPS'] = df['Price'] / df['PE']
    # Implied Forward EPS = Price / Forward_PE
    df['Forward_EPS'] = df['Price'] / df['Forward_PE']
    
    # Calculate historical statistics for Trailing PE
    mean_pe = df['PE'].mean()
    std_pe = df['PE'].std()
    min_pe = df['PE'].min()
    max_pe = df['PE'].max()
    current_pe = df['PE'].iloc[-1]
    
    # Calculate historical statistics for Forward PE
    mean_fwd_pe = df['Forward_PE'].mean()
    std_fwd_pe = df['Forward_PE'].std()
    min_fwd_pe = df['Forward_PE'].min()
    max_fwd_pe = df['Forward_PE'].max()
    current_fwd_pe = df['Forward_PE'].iloc[-1]
    
    current_price = df['Price'].iloc[-1]
    current_date = df['Date'].iloc[-1]
    
    # Calculate PE percentiles
    pe_percentile = (df['PE'] < current_pe).mean() * 100
    fwd_pe_percentile = (df['Forward_PE'] < current_fwd_pe).mean() * 100
    
    print("\n" + "="*60)
    print(f"      {index_name} INDEX VALUATION STATISTICS (20 YEARS)")
    print("="*60)
    print(f"Analysis Period:         {df['Date'].iloc[0]} to {current_date}")
    print(f"Current Price:           {current_price:,.2f}")
    print(f"Current Trailing P/E:    {current_pe:.2f} (Mean: {mean_pe:.2f}, SD: {std_pe:.2f})")
    print(f"Current Forward P/E:     {current_fwd_pe:.2f} (Mean: {mean_fwd_pe:.2f}, SD: {std_fwd_pe:.2f})")
    print(f"Trailing P/E Percentile: {pe_percentile:.1f}%")
    print(f"Forward P/E Percentile:  {fwd_pe_percentile:.1f}%")
    print("="*60 + "\n")
    
    # Calculate Trailing Fixed Bands
    for pe_val in fixed_pe_levels:
        df[f'Band_{pe_val}x'] = df['EPS'] * pe_val
        
    # Calculate Forward Fixed Bands
    for pe_val in fixed_pe_levels:
        df[f'Band_fwd_{pe_val}x'] = df['Forward_EPS'] * pe_val
        
    # Calculate Trailing SD-based PE levels
    sd_levels = {
        'SD_minus_2': mean_pe - 2 * std_pe,
        'SD_minus_1': mean_pe - 1 * std_pe,
        'SD_mean': mean_pe,
        'SD_plus_1': mean_pe + 1 * std_pe,
        'SD_plus_2': mean_pe + 2 * std_pe
    }
    for label, pe_val in sd_levels.items():
        pe_val = max(1.0, pe_val)
        df[label] = df['EPS'] * pe_val
        
    # Calculate Forward SD-based PE levels
    fwd_sd_levels = {
        'SD_fwd_minus_2': mean_fwd_pe - 2 * std_fwd_pe,
        'SD_fwd_minus_1': mean_fwd_pe - 1 * std_fwd_pe,
        'SD_fwd_mean': mean_fwd_pe,
        'SD_fwd_plus_1': mean_fwd_pe + 1 * std_fwd_pe,
        'SD_fwd_plus_2': mean_fwd_pe + 2 * std_fwd_pe
    }
    for label, pe_val in fwd_sd_levels.items():
        pe_val = max(1.0, pe_val)
        df[label] = df['Forward_EPS'] * pe_val
        
    stats = {
        'mean_pe': mean_pe,
        'std_pe': std_pe,
        'sd_levels': sd_levels,
        'mean_fwd_pe': mean_fwd_pe,
        'std_fwd_pe': std_fwd_pe,
        'fwd_sd_levels': fwd_sd_levels
    }
    return df, stats

def plot_fixed_river(df, mean_pe, index_name="SOX", fixed_pe_levels=[15, 20, 25, 30, 35, 40], is_forward=False, footnote=None):
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    dates = pd.to_datetime(df['Date'])
    
    # Color scheme for Fixed P/E Bands (smooth transitioning translucency)
    colors = {
        'band0': '#1a365d',  # Deep Blue
        'band1': '#2a4365',  # Navy
        'band2': '#2c7a7b',  # Teal/Blue-Green
        'band3': '#2f855a',  # Green
        'band4': '#744210',  # Amber
        'band5': '#742a2a',  # Red
    }
    
    # Fill standard P/E bands (creating the river)
    b0, b1, b2, b3, b4, b5 = fixed_pe_levels
    suffix = "fwd_" if is_forward else ""
    band_b0 = f'Band_{suffix}{b0}x'
    band_b1 = f'Band_{suffix}{b1}x'
    band_b2 = f'Band_{suffix}{b2}x'
    band_b3 = f'Band_{suffix}{b3}x'
    band_b4 = f'Band_{suffix}{b4}x'
    band_b5 = f'Band_{suffix}{b5}x'
    
    pe_type = "Rolling 12M Forward" if is_forward else "Trailing"
    pe_col = 'Forward_PE' if is_forward else 'PE'
    
    ax.fill_between(dates, df[band_b0], df[band_b1], color=colors['band0'], alpha=0.6, label=f'{b0}x - {b1}x Forward P/E (Undervalued)' if is_forward else f'{b0}x - {b1}x P/E (Undervalued)')
    ax.fill_between(dates, df[band_b1], df[band_b2], color=colors['band1'], alpha=0.6, label=f'{b1}x - {b2}x Forward P/E (Fair Lower)' if is_forward else f'{b1}x - {b2}x P/E (Fair Lower)')
    ax.fill_between(dates, df[band_b2], df[band_b3], color=colors['band2'], alpha=0.6, label=f'{b2}x - {b3}x Forward P/E (Fair Upper)' if is_forward else f'{b2}x - {b3}x P/E (Fair Upper)')
    ax.fill_between(dates, df[band_b3], df[band_b4], color=colors['band3'], alpha=0.6, label=f'{b3}x - {b4}x Forward P/E (Overvalued)' if is_forward else f'{b3}x - {b4}x P/E (Overvalued)')
    ax.fill_between(dates, df[band_b4], df[band_b5], color=colors['band4'], alpha=0.6, label=f'{b4}x - {b5}x Forward P/E (Highly Overvalued)' if is_forward else f'{b4}x - {b5}x P/E (Highly Overvalued)')
    
    # Plot band lines
    for pe_val in fixed_pe_levels:
        col_name = f'Band_{suffix}{pe_val}x'
        ax.plot(dates, df[col_name], color='white', alpha=0.15, linestyle='--', linewidth=0.8)
        # Label the band line at the rightmost edge
        ax.text(dates.iloc[-1], df[col_name].iloc[-1], f' {pe_val}x', color='#a0aec0', fontsize=8, va='center')
        
    # Plot Index Price Close Line (thick glowing cyan line)
    ax.plot(dates, df['Price'], color='#00f2fe', linewidth=2.5, label=f'{index_name} Index Price')
    
    # Customizing axes
    title_str = f'{index_name} Index {pe_type} P/E River Chart (Fixed Multipliers - 20 Years)'
    ax.set_title(title_str, fontsize=16, fontweight='bold', pad=20, color='#f7fafc')
    ax.set_xlabel('Year', fontsize=12, labelpad=10, color='#a0aec0')
    ax.set_ylabel('Index Value', fontsize=12, labelpad=10, color='#a0aec0')
    
    # Format x-axis dates
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.xticks(rotation=0)
    
    # Grid lines
    ax.grid(True, which='both', linestyle=':', color='#2d3748', alpha=0.5)
    
    # Add stats box
    stats_text = (
        f"Latest Date: {df['Date'].iloc[-1]}\n"
        f"{index_name} Price: {df['Price'].iloc[-1]:,.2f}\n"
        f"{index_name} {pe_type} P/E: {df[pe_col].iloc[-1]:.2f}x\n"
        f"20-Yr Avg {pe_type} P/E: {mean_pe:.2f}x"
    )
    props = dict(boxstyle='round,pad=0.8', facecolor='#1a202c', edgecolor='#4a5568', alpha=0.8)
    ax.text(0.02, 0.95, stats_text, transform=ax.transAxes, fontsize=10, verticalalignment='top', bbox=props, color='#e2e8f0')
    
    # Customize Legend
    ax.legend(loc='lower right', facecolor='#1a202c', edgecolor='#4a5568', labelcolor='#e2e8f0', framealpha=0.9)
    
    # Formatting Layout
    plt.tight_layout()
    
    # Optional footnote at bottom of figure
    if footnote:
        plt.figtext(0.5, -0.03, footnote, ha='center', va='top',
                    fontproperties=_CJK_FONT, color='#718096', wrap=True,
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='#1a202c', edgecolor='#2d3748', alpha=0.7))
        plt.subplots_adjust(bottom=0.14)
    
    # Save Image
    out_file = f'{index_name.lower()}_pe_river_fwd_fixed.png' if is_forward else f'{index_name.lower()}_pe_river_fixed.png'
    plt.savefig(out_file, facecolor='#121212', edgecolor='none', bbox_inches='tight')
    print(f"Generated {pe_type} Fixed Multipliers River Chart: {os.path.abspath(out_file)}")
    plt.close()

def plot_sd_river(df, mean_pe, std_pe, sd_levels, index_name="SOX", is_forward=False, footnote=None):
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    dates = pd.to_datetime(df['Date'])
    
    # SD Band colors
    colors = {
        'minus2_to_minus1': '#1a365d',  # Deep Blue (Undervalued)
        'minus1_to_mean': '#2c7a7b',    # Teal (Slightly Undervalued)
        'mean_to_plus1': '#2f855a',     # Green (Slightly Overvalued)
        'plus1_to_plus2': '#744210',    # Amber (Overvalued)
        'above_plus2': '#742a2a'        # Red (Bubble)
    }
    
    pe_type = "Rolling 12M Forward" if is_forward else "Trailing"
    pe_col = 'Forward_PE' if is_forward else 'PE'
    
    keys = {
        'm2': 'SD_fwd_minus_2' if is_forward else 'SD_minus_2',
        'm1': 'SD_fwd_minus_1' if is_forward else 'SD_minus_1',
        'mean': 'SD_fwd_mean' if is_forward else 'SD_mean',
        'p1': 'SD_fwd_plus_1' if is_forward else 'SD_plus_1',
        'p2': 'SD_fwd_plus_2' if is_forward else 'SD_plus_2'
    }
    
    # Fill bands
    ax.fill_between(dates, df[keys['m2']], df[keys['m1']], color=colors['minus2_to_minus1'], alpha=0.6, 
                    label=f'-2 SD to -1 SD ({sd_levels[keys["m2"]]:.1f}x - {sd_levels[keys["m1"]]:.1f}x)')
    ax.fill_between(dates, df[keys['m1']], df[keys['mean']], color=colors['minus1_to_mean'], alpha=0.6, 
                    label=f'-1 SD to Mean ({sd_levels[keys["m1"]]:.1f}x - {sd_levels[keys["mean"]]:.1f}x)')
    ax.fill_between(dates, df[keys['mean']], df[keys['p1']], color=colors['mean_to_plus1'], alpha=0.6, 
                    label=f'Mean to +1 SD ({sd_levels[keys["mean"]]:.1f}x - {sd_levels[keys["p1"]]:.1f}x)')
    ax.fill_between(dates, df[keys['p1']], df[keys['p2']], color=colors['plus1_to_plus2'], alpha=0.6, 
                    label=f'+1 SD to +2 SD ({sd_levels[keys["p1"]]:.1f}x - {sd_levels[keys["p2"]]:.1f}x)')
    
    # Plot SD lines
    sd_line_labels = [
        (keys['m2'], '-2 SD'),
        (keys['m1'], '-1 SD'),
        (keys['mean'], 'Mean PE'),
        (keys['p1'], '+1 SD'),
        (keys['p2'], '+2 SD')
    ]
    for key, label in sd_line_labels:
        is_mean = (key == keys['mean'])
        line_color = '#cbd5e0' if is_mean else '#a0aec0'
        line_style = '-' if is_mean else '--'
        line_width = 1.2 if is_mean else 0.8
        line_alpha = 0.4 if is_mean else 0.2
        
        ax.plot(dates, df[key], color=line_color, linestyle=line_style, linewidth=line_width, alpha=line_alpha)
        # Label each line on the right edge
        ax.text(dates.iloc[-1], df[key].iloc[-1], f' {label} ({sd_levels[key]:.1f}x)', color='#a0aec0', fontsize=8, va='center')
        
    # Plot Price Close Line
    ax.plot(dates, df['Price'], color='#00f2fe', linewidth=2.5, label=f'{index_name} Index Price')
    
    # Customizing axes
    title_str = f'{index_name} Index {pe_type} P/E River Chart (Standard Deviation Bands - 20 Years)'
    ax.set_title(title_str, fontsize=16, fontweight='bold', pad=20, color='#f7fafc')
    ax.set_xlabel('Year', fontsize=12, labelpad=10, color='#a0aec0')
    ax.set_ylabel('Index Value', fontsize=12, labelpad=10, color='#a0aec0')
    
    # Format x-axis dates
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.xticks(rotation=0)
    
    # Grid lines
    ax.grid(True, which='both', linestyle=':', color='#2d3748', alpha=0.5)
    
    # Add stats box
    stats_text = (
        f"Latest Date: {df['Date'].iloc[-1]}\n"
        f"{index_name} Price: {df['Price'].iloc[-1]:,.2f}\n"
        f"{index_name} {pe_type} P/E: {df[pe_col].iloc[-1]:.2f}x\n"
        f"20-Yr Mean {pe_type} P/E: {mean_pe:.2f}x\n"
        f"1 Standard Dev: ±{std_pe:.2f}x"
    )
    props = dict(boxstyle='round,pad=0.8', facecolor='#1a202c', edgecolor='#4a5568', alpha=0.8)
    ax.text(0.02, 0.95, stats_text, transform=ax.transAxes, fontsize=10, verticalalignment='top', bbox=props, color='#e2e8f0')
    
    # Customize Legend
    ax.legend(loc='lower right', facecolor='#1a202c', edgecolor='#4a5568', labelcolor='#e2e8f0', framealpha=0.9)
    
    # Formatting Layout
    plt.tight_layout()
    
    # Optional footnote at bottom of figure
    if footnote:
        plt.figtext(0.5, -0.03, footnote, ha='center', va='top',
                    fontproperties=_CJK_FONT, color='#718096', wrap=True,
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='#1a202c', edgecolor='#2d3748', alpha=0.7))
        plt.subplots_adjust(bottom=0.14)
    
    # Save Image
    out_file = f'{index_name.lower()}_pe_river_fwd_sd.png' if is_forward else f'{index_name.lower()}_pe_river_sd.png'
    plt.savefig(out_file, facecolor='#121212', edgecolor='none', bbox_inches='tight')
    print(f"Generated {pe_type} SD-Bands River Chart: {os.path.abspath(out_file)}")
    plt.close()

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

def plot_pe_trend(df, mean_pe, std_pe, sd_levels, index_name="SOX", is_forward=False, footnote=None, years_to_plot=5):
    with plt.style.context('default'):
        # Set size to 1200x500 pixels (figsize=(12, 5) at 100 DPI)
        fig, ax = plt.subplots(figsize=(12, 5), dpi=100, facecolor='white')
        ax.set_facecolor('white')
        
        # Slice to last 5 years for plotting
        df_plot = df.copy()
        df_plot['Date_dt'] = pd.to_datetime(df_plot['Date'])
        max_date = df_plot['Date_dt'].max()
        cutoff_date = max_date - pd.DateOffset(years=years_to_plot)
        df_plot = df_plot[df_plot['Date_dt'] >= cutoff_date]
        
        dates = df_plot['Date_dt']
        pe_type = "Rolling 12M Forward" if is_forward else "Trailing"
        pe_col = 'Forward_PE' if is_forward else 'PE'
        
        # Get index colors
        colors = INDEX_TREND_COLORS.get(index_name, {
            "primary": "#c084fc",
            "mean": "black",
            "sd_1": "grey",
            "sd_2": "lightgrey"
        })
        
        # Plot P/E Trend (last 5 years)
        ax.plot(dates, df_plot[pe_col], color=colors["primary"], linewidth=3.0, label=f'{index_name} {pe_type} P/E Ratio')
        
        # Draw horizontal boundary lines (reference boundaries are still calculated from 20-year data)
        ax.axhline(mean_pe, color=colors["mean"], alpha=0.8, linestyle='-', linewidth=2.0, label=f'20-Yr Average ({mean_pe:.2f}x)')
        ax.axhline(mean_pe + std_pe, color=colors["sd_1"], alpha=0.7, linestyle='--', linewidth=1.5, label=f'+1 SD ({(mean_pe + std_pe):.2f}x)')
        ax.axhline(mean_pe - std_pe, color=colors["sd_1"], alpha=0.7, linestyle='--', linewidth=1.5, label=f'-1 SD ({(mean_pe - std_pe):.2f}x)')
        ax.axhline(mean_pe + 2 * std_pe, color=colors["sd_2"], alpha=0.6, linestyle='-.', linewidth=1.5, label=f'+2 SD ({(mean_pe + 2*std_pe):.2f}x)')
        ax.axhline(mean_pe - 2 * std_pe, color=colors["sd_2"], alpha=0.6, linestyle='-.', linewidth=1.5, label=f'-2 SD ({(mean_pe - 2*std_pe):.2f}x)')
        
        # Customizing axes for light theme
        title_str = f'{index_name} Index Historical {pe_type} P/E Trend & Valuation Boundaries ({years_to_plot} Years)'
        ax.set_title(title_str, fontsize=16, fontweight='bold', pad=20, color='#1e293b')
        ax.set_xlabel('Year', fontsize=12, labelpad=10, color='#334155')
        ax.set_ylabel(f'{pe_type} P/E Ratio', fontsize=12, labelpad=10, color='#334155')
        
        # Format x-axis dates with 1-year ticks
        ax.xaxis.set_major_locator(mdates.YearLocator(1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        plt.xticks(rotation=0)
        
        # Set tick parameters for light theme
        ax.tick_params(colors='#334155', labelsize=10)
        ax.spines['bottom'].set_color('#cbd5e1')
        ax.spines['left'].set_color('#cbd5e1')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Light grid
        ax.grid(True, which='both', linestyle=':', color='#e2e8f0', alpha=0.8)
        
        # Customize Legend (light theme)
        ax.legend(loc='lower left', facecolor='white', edgecolor='#cbd5e1', labelcolor='#334155', framealpha=0.95, ncol=3, fontsize=9)
        
        plt.tight_layout()
        
        # Optional footnote at bottom of figure (light theme)
        if footnote:
            plt.figtext(0.5, -0.04, footnote, ha='center', va='top',
                        fontproperties=_CJK_FONT, color='#475569', wrap=True,
                        bbox=dict(boxstyle='round,pad=0.4', facecolor='#f8fafc', edgecolor='#cbd5e1', alpha=0.9))
            plt.subplots_adjust(bottom=0.18)
        
        # Save Image with white background
        out_file = f'{index_name.lower()}_pe_fwd_trend.png' if is_forward else f'{index_name.lower()}_pe_trend.png'
        plt.savefig(out_file, facecolor='white', edgecolor='none', bbox_inches='tight')
        print(f"Generated {pe_type} P/E Trend Chart: {os.path.abspath(out_file)}")
        plt.close()

# Footnote text for IXIC — explains the data cleaning applied, and why it differs from standard methods.
IXIC_FOOTNOTE = (
    "※ 數據修正說明｜LSEG 資料庫於 2024 年 1 月至 2025 年 6 月間，多次回傳 Nasdaq Composite 本益比異常低值（最低達 8～14 倍），"
    "與市場實況（正常應在 25～35 倍）嚴重背離，為資料庫計算錯誤所致。"
    "本圖採「絕對下限過濾（min P/E = 21x）」剔除異常值後，以線性插補（Linear Interpolation）進行平滑填補。"
    "與常見的前值沿用（Forward Fill）相比，線性插補可在修正邊界避免階梯狀跳躍，使河流帶型連貫平滑。"
    "插補區間內之數值為估算值，非實際觀測數據。"
)

def main():
    freq_label = f"週頻 (Weekly)" if FREQ == "W" else "月頻 (Monthly)"
    print(f"\n{'='*60}")
    print(f"  plot_river.py  |  Frq = {FREQ}  ({freq_label})")
    print(f"{'='*60}")
    
    indices = [
        {"name": "SOX",  "csv": f"sox_pe_data_{FREQ}.csv",  "fixed_bands": [15, 20, 25, 30, 35, 40], "min_val": 12.0, "footnote": None},
        {"name": "SOX_YF", "csv": f"sox_yf_pe_data_{FREQ}.csv", "fixed_bands": [15, 20, 25, 30, 35, 40], "min_val": 12.0, "footnote": None},
        {"name": "SPX",  "csv": f"spx_pe_data_{FREQ}.csv",  "fixed_bands": [12, 15, 18, 21, 24, 27], "min_val": 12.0, "footnote": None},
        {"name": "IXIC", "csv": f"ixic_pe_data_{FREQ}.csv", "fixed_bands": [15, 20, 25, 30, 35, 40], "min_val": 21.0, "footnote": IXIC_FOOTNOTE},
        {"name": "DJI",  "csv": f"dji_pe_data_{FREQ}.csv",  "fixed_bands": [10, 13, 16, 19, 22, 25], "min_val": 12.0, "footnote": None}
    ]
    
    for ind in indices:
        csv_file = ind["csv"]
        name = ind["name"]
        fixed_bands = ind["fixed_bands"]
        min_val = ind["min_val"]
        footnote = ind["footnote"]
        
        if not os.path.exists(csv_file):
            print(f"\n⚠️  {csv_file} not found. Skipping {name}.")
            print(f"   → Run query_all.py with FREQ='{FREQ}' first.")
            continue
            
        print(f"\nProcessing index: {name} from {csv_file}")
        df = pd.read_csv(csv_file)
        
        # Process and calculate bands (both trailing and forward)
        df, stats = calculate_river_bands(df, index_name=name, fixed_pe_levels=fixed_bands, min_val=min_val)
        
        # Generate Trailing charts
        plot_fixed_river(df, stats['mean_pe'], index_name=name, fixed_pe_levels=fixed_bands, is_forward=False, footnote=footnote)
        plot_sd_river(df, stats['mean_pe'], stats['std_pe'], stats['sd_levels'], index_name=name, is_forward=False, footnote=footnote)
        plot_pe_trend(df, stats['mean_pe'], stats['std_pe'], stats['sd_levels'], index_name=name, is_forward=False, footnote=footnote)
        
        # Generate Forward charts
        plot_fixed_river(df, stats['mean_fwd_pe'], index_name=name, fixed_pe_levels=fixed_bands, is_forward=True, footnote=footnote)
        plot_sd_river(df, stats['mean_fwd_pe'], stats['std_fwd_pe'], stats['fwd_sd_levels'], index_name=name, is_forward=True, footnote=footnote)
        plot_pe_trend(df, stats['mean_fwd_pe'], stats['std_fwd_pe'], stats['fwd_sd_levels'], index_name=name, is_forward=True, footnote=footnote)
        
        # Save processed dataframe with bands (freq-suffixed)
        out_csv = f"{name.lower()}_pe_river_data_{FREQ}.csv"
        df.to_csv(out_csv, index=False)
        print(f"Saved processed data with bands to: {os.path.abspath(out_csv)}")

if __name__ == "__main__":
    main()
