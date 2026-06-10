import yfinance as yf
import pandas as pd

# SOX (Philadelphia Semiconductor Index) - 30 components
# Source: PHLX Semiconductor Sector Index
SOX_COMPONENTS = [
    'NVDA', 'AVGO', 'AMD',  'QCOM', 'AMAT',
    'LRCX', 'KLAC', 'MU',   'TXN',  'ADI',
    'MCHP', 'ON',   'MRVL', 'NXPI', 'MPWR',
    'SWKS', 'QRVO', 'TER',  'ENTG', 'STM',
    'ASML', 'INTC', 'MKSI', 'WOLF', 'ACLS',
    'CAMT', 'FORM', 'SITM', 'RMBS', 'COHU'
]

print("=" * 65)
print("  SOX Forward PE — Bottom-Up Calculation via yfinance")
print("=" * 65)
print(f"  Fetching data for {len(SOX_COMPONENTS)} components...\n")

rows = []
missing_fwd = []
missing_trail = []

for tkr in SOX_COMPONENTS:
    try:
        info = yf.Ticker(tkr).info
        price       = info.get('currentPrice') or info.get('regularMarketPrice')
        fwd_eps     = info.get('forwardEps')
        trail_eps   = info.get('trailingEps')
        trail_pe    = info.get('trailingPE')
        fwd_pe      = info.get('forwardPE')
        name        = info.get('shortName', tkr)

        rows.append({
            'Ticker':    tkr,
            'Name':      name,
            'Price':     price,
            'Trail_EPS': trail_eps,
            'Fwd_EPS':   fwd_eps,
            'Trail_PE':  trail_pe,
            'Fwd_PE':    fwd_pe,
        })

        if fwd_eps is None:
            missing_fwd.append(tkr)
        if trail_eps is None:
            missing_trail.append(tkr)

        status = "OK" if (fwd_eps and trail_eps) else "??"
        print(f"  {status} {tkr:<6}  Price={price or 'N/A':>10}  "
              f"TrailEPS={str(trail_eps or 'N/A'):>8}  "
              f"FwdEPS={str(fwd_eps or 'N/A'):>8}")
    except Exception as e:
        print(f"  !! {tkr:<6}  ERROR: {e}")
        missing_fwd.append(tkr)
        missing_trail.append(tkr)

# ── Build DataFrame ────────────────────────────────────────────
df = pd.DataFrame(rows).dropna(subset=['Price'])

# ── Trailing PE (Aggregate / Pooled method) ────────────────────
df_trail = df.dropna(subset=['Trail_EPS'])
total_price_t  = df_trail['Price'].sum()
total_eps_t    = df_trail['Trail_EPS'].sum()
sox_trail_pe   = total_price_t / total_eps_t

# ── Forward PE (Aggregate / Pooled method) ─────────────────────
df_fwd = df.dropna(subset=['Fwd_EPS'])
total_price_f  = df_fwd['Price'].sum()
total_eps_f    = df_fwd['Fwd_EPS'].sum()
sox_fwd_pe     = total_price_f / total_eps_f

# ── Print Summary ──────────────────────────────────────────────
print()
print("=" * 65)
print("  RESULTS")
print("=" * 65)
print(f"  Stocks with Trailing EPS data : {len(df_trail)}/{len(SOX_COMPONENTS)}")
print(f"  Stocks with Forward  EPS data : {len(df_fwd)}/{len(SOX_COMPONENTS)}")
if missing_trail:
    print(f"  Missing Trailing EPS : {', '.join(missing_trail)}")
if missing_fwd:
    print(f"  Missing Forward  EPS : {', '.join(missing_fwd)}")
print()
print(f"  ★ SOX Trailing PE (Bottom-Up, GAAP) : {sox_trail_pe:>8.2f}x")
print(f"  ★ SOX Forward  PE (Bottom-Up, GAAP) : {sox_fwd_pe:>8.2f}x")
print()
print("  Benchmark comparison:")
print(f"  - LSEG  Trailing PE (Non-GAAP)      :    65.32x")
print(f"  - iShares SOXX PE   (GAAP)           :    80.05x")
print(f"  - Our   Trailing PE (GAAP, yfinance) : {sox_trail_pe:>8.2f}x  ← 預期接近 iShares")
print("=" * 65)
