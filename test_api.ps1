try {
    $t = Invoke-RestMethod -Uri 'https://api.tiingo.com/tiingo/daily/soxx/prices?startDate=2026-05-01&token=9422f5fb1bda476da32ae9b42ba4ea097b9b3f94' -UserAgent 'Mozilla/5.0'
    Write-Output "Tiingo Success!"
    $t | ConvertTo-Json -Depth 2
} catch {
    Write-Output "Tiingo Error: $($_.Exception.Message)"
}

try {
    $e = Invoke-RestMethod -Uri 'https://eodhistoricaldata.com/api/eod/SOXX.US?api_token=9422f5fb1bda476da32ae9b42ba4ea097b9b3f94&fmt=json' -UserAgent 'Mozilla/5.0'
    Write-Output "EOD Success!"
    $e[0..2] | ConvertTo-Json -Depth 2
} catch {
    Write-Output "EOD Error: $($_.Exception.Message)"
}
