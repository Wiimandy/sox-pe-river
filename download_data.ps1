try {
    # Download ^SOX (Philadelphia Semiconductor Index) monthly prices for the last 10 years
    $soxUrl = "https://query1.finance.yahoo.com/v8/finance/chart/^SOX?range=10y&interval=1mo"
    Write-Output "Downloading ^SOX historical chart data..."
    $soxData = Invoke-RestMethod -Uri $soxUrl -UserAgent "Mozilla/5.0"
    $soxData | ConvertTo-Json -Depth 10 | Out-File -FilePath "C:\Users\User\.gemini\antigravity\scratch\sox-pe-river\sox_raw.json" -Encoding utf8
    Write-Output "Downloaded ^SOX raw data successfully."
} catch {
    Write-Output "Error downloading ^SOX data: $($_.Exception.Message)"
}

try {
    # Download SOXX (iShares Semiconductor ETF) monthly prices for the last 10 years
    $soxxUrl = "https://query1.finance.yahoo.com/v8/finance/chart/SOXX?range=10y&interval=1mo"
    Write-Output "Downloading SOXX historical chart data..."
    $soxxData = Invoke-RestMethod -Uri $soxxUrl -UserAgent "Mozilla/5.0"
    $soxxData | ConvertTo-Json -Depth 10 | Out-File -FilePath "C:\Users\User\.gemini\antigravity\scratch\sox-pe-river\soxx_raw.json" -Encoding utf8
    Write-Output "Downloaded SOXX raw data successfully."
} catch {
    Write-Output "Error downloading SOXX data: $($_.Exception.Message)"
}
