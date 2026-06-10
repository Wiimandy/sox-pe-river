// Index P/E River Chart - Dashboard Application Logic

document.addEventListener('DOMContentLoaded', () => {
    // --- 1. Validate Data Load ---
    if (typeof SOX_DATA === 'undefined' || typeof SPX_DATA === 'undefined' || typeof IXIC_DATA === 'undefined' || typeof DJI_DATA === 'undefined') {
        console.error("Error: SOX_DATA, SPX_DATA, IXIC_DATA, or DJI_DATA is not loaded. Please ensure data.js exists and is populated.");
        return;
    }

    // --- 2. DOM Elements ---
    const valPrice = document.getElementById('val-price');
    const valDate = document.getElementById('val-date');
    const valPe = document.getElementById('val-pe');
    const valForwardPe = document.getElementById('val-forward-pe');
    const valMeanPe = document.getElementById('val-mean-pe');
    const valStdPe = document.getElementById('val-std-pe');
    const valPercentile = document.getElementById('val-percentile');
    const valStatus = document.getElementById('val-status');
    
    const btnSD = document.getElementById('btn-sd');
    const btnFixed = document.getElementById('btn-fixed');
    const btnResetZoom = document.getElementById('btn-reset-zoom');
    
    const btnSOX = document.getElementById('btn-sox');
    const btnSPX = document.getElementById('btn-spx');
    const btnIXIC = document.getElementById('btn-ixic');
    const btnDJI = document.getElementById('btn-dji');
    
    const btnTrailing = document.getElementById('btn-trailing');
    const btnForward = document.getElementById('btn-forward');
    
    const appTitleIndex = document.getElementById('app-title-index');
    const appSubtitleDesc = document.getElementById('app-subtitle-desc');
    const chartMainTitle = document.getElementById('chart-main-title');
    const chartPeTitle = document.getElementById('chart-pe-title');
    const chartPeSubtitle = document.getElementById('chart-pe-subtitle');
    
    const lblPrice = document.getElementById('lbl-price');
    const lblPe = document.getElementById('lbl-pe');
    const lblStats = document.getElementById('lbl-stats');
    
    const btnRefreshData = document.getElementById('btn-refresh-data');
    const btnExportCharts = document.getElementById('btn-export-charts');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    
    // --- 3. State Management ---
    let activeIndexName = 'SOX'; // 'SOX', 'SPX', 'IXIC', 'DJI'
    let activeDataset = SOX_DATA;
    let currentMode = 'sd'; // 'sd' or 'fixed'
    let currentMetric = 'trailing'; // 'trailing' or 'forward'
    
    let currentChart = null;
    let peChart = null;
    
    // --- 4. Dashboard Update Logic ---
    function updateDashboard(indexName, metricName = currentMetric) {
        activeIndexName = indexName;
        currentMetric = metricName;
        
        const datasetMap = {
            'SOX': SOX_DATA,
            'SPX': SPX_DATA,
            'IXIC': IXIC_DATA,
            'DJI': DJI_DATA
        };
        activeDataset = datasetMap[indexName];
        
        // Calculate Statistics
        const latestData = activeDataset[activeDataset.length - 1];
        const prices = activeDataset.map(d => d.Price);
        const pes = currentMetric === 'trailing' ? activeDataset.map(d => d.PE) : activeDataset.map(d => d.Forward_PE);
        const dates = activeDataset.map(d => d.Date);
        
        const sumPE = pes.reduce((a, b) => a + b, 0);
        const meanPE = sumPE / pes.length;
        
        const variancePE = pes.reduce((a, b) => a + Math.pow(b - meanPE, 2), 0) / pes.length;
        const stdPE = Math.sqrt(variancePE);
        
        const currentPE = currentMetric === 'trailing' ? latestData.PE : latestData.Forward_PE;
        const lowerPECount = pes.filter(pe => pe < currentPE).length;
        const percentile = (lowerPECount / pes.length) * 100;
        
        // Update Title & Subtitle descriptions
        const peLabel = currentMetric === 'trailing' ? '歷史本益比 (PE)' : '滾動 12 個月預估本益比 (Rolling 12-Month Forward PE)';
        const peShortLabel = currentMetric === 'trailing' ? 'PE' : 'Rolling 12M Fwd PE';
        
        if (indexName === 'SOX') {
            appTitleIndex.textContent = 'SOX';
            appSubtitleDesc.textContent = `費城半導體指數 20 年${peLabel}河流圖及估值分析儀表板`;
            lblPrice.textContent = 'SOX 指數最新價格';
            lblPe.textContent = `當前${peLabel}`;
            lblStats.textContent = `20 年歷史平均 ${peShortLabel}`;
            chartPeTitle.textContent = `SOX 指數歷史${peLabel}走勢與估值區間`;
            chartPeSubtitle.textContent = `呈現過去 20 年費半指數 ${peShortLabel} 值波動，並以橫線標示歷史均值與 ±1、±2 標準差估值邊界。`;
        } else if (indexName === 'SPX') {
            appTitleIndex.textContent = 'S&P 500';
            appSubtitleDesc.textContent = `標普 500 指數 20 年${peLabel}河流圖及估值分析儀表板`;
            lblPrice.textContent = 'S&P 500 指數最新價格';
            lblPe.textContent = `當前${peLabel}`;
            lblStats.textContent = `20 年歷史平均 ${peShortLabel}`;
            chartPeTitle.textContent = `S&P 500 指數歷史${peLabel}走勢與估值區間`;
            chartPeSubtitle.textContent = `呈現過去 20 年標普 500 指數 ${peShortLabel} 值波動，並以橫線標示歷史均值與 ±1、±2 標準差估值邊界。`;
        } else if (indexName === 'IXIC') {
            appTitleIndex.textContent = 'NASDAQ';
            appSubtitleDesc.textContent = `納斯達克綜合指數 20 年${peLabel}河流圖及估值分析儀表板`;
            lblPrice.textContent = 'NASDAQ 指數最新價格';
            lblPe.textContent = `當前${peLabel}`;
            lblStats.textContent = `20 年歷史平均 ${peShortLabel}`;
            chartPeTitle.textContent = `NASDAQ 指數歷史${peLabel}走勢與估值區間`;
            chartPeSubtitle.textContent = `呈現過去 20 年納斯達克指數 ${peShortLabel} 值波動，並以橫線標示歷史均值與 ±1、±2 標準差估值邊界。`;
        } else if (indexName === 'DJI') {
            appTitleIndex.textContent = 'Dow Jones';
            appSubtitleDesc.textContent = `道瓊工業平均指數 20 年${peLabel}河流圖及估值分析儀表板`;
            lblPrice.textContent = 'Dow Jones 指數最新價格';
            lblPe.textContent = `當前${peLabel}`;
            lblStats.textContent = `20 年歷史平均 ${peShortLabel}`;
            chartPeTitle.textContent = `Dow Jones 指數歷史${peLabel}走勢與估值區間`;
            chartPeSubtitle.textContent = `呈現過去 20 年道瓊指數 ${peShortLabel} 值波動，並以橫線標示歷史均值與 ±1、±2 標準差估值邊界。`;
        }
        
        // Show/hide IXIC data correction notice
        const ixicNotice = document.getElementById('ixic-data-notice');
        if (ixicNotice) {
            if (indexName === 'IXIC') {
                ixicNotice.classList.add('visible');
            } else {
                ixicNotice.classList.remove('visible');
            }
        }
        
        // Update Stats Cards
        valPrice.textContent = Number(latestData.Price).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        valDate.textContent = `最後更新日期: ${latestData.Date}`;
        valPe.textContent = `${Number(currentPE).toFixed(2)}x`;
        
        // In trailing mode, display forward PE; in forward mode, display trailing PE in footer
        valForwardPe.textContent = currentMetric === 'trailing' ? 
            (latestData.Forward_PE ? `滾動 12M 預估本益比: ${Number(latestData.Forward_PE).toFixed(2)}x` : '滾動 12M 預估本益比: N/A') :
            (latestData.PE ? `歷史本益比 (Trailing LTM): ${Number(latestData.PE).toFixed(2)}x` : '歷史本益比 (Trailing LTM): N/A');
            
        valMeanPe.textContent = `${meanPE.toFixed(2)}x`;
        valStdPe.textContent = `標準差 (1 SD): ±${stdPE.toFixed(2)}x`;
        valPercentile.textContent = `${percentile.toFixed(1)}%`;
        
        // Calculate Valuation Status Badge
        let statusText = "";
        let statusClass = "";
        
        const sdMinus2 = meanPE - 2 * stdPE;
        const sdMinus1 = meanPE - stdPE;
        const sdPlus1 = meanPE + stdPE;
        const sdPlus2 = meanPE + 2 * stdPE;
        
        if (currentPE < sdMinus2) {
            statusText = "極度低估 (Severely Cheap)";
            statusClass = "success";
        } else if (currentPE >= sdMinus2 && currentPE < sdMinus1) {
            statusText = "低估區間 (Undervalued)";
            statusClass = "info";
        } else if (currentPE >= sdMinus1 && currentPE <= sdPlus1) {
            statusText = "合理估值 (Fair Value)";
            statusClass = "success";
        } else if (currentPE > sdPlus1 && currentPE <= sdPlus2) {
            statusText = "高估區間 (Overvalued)";
            statusClass = "warning";
        } else {
            statusText = "極度高估 (Bubble Risk)";
            statusClass = "danger";
        }
        
        valStatus.textContent = statusText;
        valStatus.className = `valuation-badge ${statusClass}`;
        
        // Render Charts
        renderCharts(prices, pes, dates, meanPE, stdPE);
    }
    
    // --- 5. Chart rendering ---
    function renderCharts(prices, pes, dates, meanPE, stdPE) {
        if (currentChart) {
            currentChart.destroy();
        }
        if (peChart) {
            peChart.destroy();
        }
        
        const ctx = document.getElementById('riverChart').getContext('2d');
        let datasets = [];
        
        const labelMap = {
            'SOX': '費半指數',
            'SPX': '標普 500',
            'IXIC': '納斯達克',
            'DJI': '道瓊指數'
        };
        const indexLabel = labelMap[activeIndexName];
        const metricSuffix = currentMetric === 'trailing' ? '(歷史)' : '(預估)';
        
        if (currentMode === 'sd') {
            chartMainTitle.textContent = `${indexLabel}綜合本益比河流圖 (標準差區間法)`;
            
            const keyPrefix = currentMetric === 'trailing' ? 'SD_' : 'SD_fwd_';
            
            datasets = [
                {
                    label: `-2 SD 估值線 ${metricSuffix}`,
                    data: activeDataset.map(d => d[keyPrefix + 'minus_2']),
                    borderColor: 'rgba(99, 102, 241, 0.15)',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: `-1 SD 估值線 ${metricSuffix} (-2 SD ~ -1 SD 低估)`,
                    data: activeDataset.map(d => d[keyPrefix + 'minus_1']),
                    borderColor: 'rgba(20, 184, 166, 0.15)',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: 0,
                    backgroundColor: 'rgba(30, 58, 138, 0.5)'
                },
                {
                    label: `平均估值線 ${metricSuffix} (-1 SD ~ 平均值 合理偏低)`,
                    data: activeDataset.map(d => d[keyPrefix + 'mean']),
                    borderColor: 'rgba(248, 250, 252, 0.3)',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: 1,
                    backgroundColor: 'rgba(20, 184, 166, 0.45)'
                },
                {
                    label: `+1 SD 估值線 ${metricSuffix} (平均值 ~ +1 SD 合理偏高)`,
                    data: activeDataset.map(d => d[keyPrefix + 'plus_1']),
                    borderColor: 'rgba(245, 158, 11, 0.15)',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: 2,
                    backgroundColor: 'rgba(16, 185, 129, 0.42)'
                },
                {
                    label: `+2 SD 估值線 ${metricSuffix} (+1 SD ~ +2 SD 高估)`,
                    data: activeDataset.map(d => d[keyPrefix + 'plus_2']),
                    borderColor: 'rgba(239, 68, 68, 0.15)',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: 3,
                    backgroundColor: 'rgba(245, 158, 11, 0.42)'
                },
                {
                    label: `${indexLabel}收盤價 (Index Price)`,
                    data: prices,
                    borderColor: varColor('--accent-cyan'),
                    borderWidth: 2.5,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: varColor('--accent-cyan'),
                    pointHoverBorderColor: '#ffffff',
                    pointHoverBorderWidth: 2,
                    fill: false,
                    yAxisID: 'y'
                }
            ];
        } else {
            chartMainTitle.textContent = `${indexLabel}綜合本益比河流圖 (固定倍數法)`;
            
            const fixedLevelsMap = {
                'SOX': [15, 20, 25, 30, 35, 40],
                'SPX': [12, 15, 18, 21, 24, 27],
                'IXIC': [15, 20, 25, 30, 35, 40],
                'DJI': [10, 13, 16, 19, 22, 25]
            };
            const fixedLevels = fixedLevelsMap[activeIndexName];
            const l = fixedLevels;
            const keyPrefix = currentMetric === 'trailing' ? 'Band_' : 'Band_fwd_';
            
            datasets = [
                {
                    label: `${l[0]}x PE 估值線 ${metricSuffix}`,
                    data: activeDataset.map(d => d[`${keyPrefix}${l[0]}x`]),
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    borderDash: [3, 3],
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: `${l[1]}x PE 估值線 ${metricSuffix} (${l[0]}x ~ ${l[1]}x 便宜區)`,
                    data: activeDataset.map(d => d[`${keyPrefix}${l[1]}x`]),
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    borderDash: [3, 3],
                    pointRadius: 0,
                    fill: 0,
                    backgroundColor: 'rgba(26, 54, 93, 0.5)'
                },
                {
                    label: `${l[2]}x PE 估值線 ${metricSuffix} (${l[1]}x ~ ${l[2]}x 合理偏低)`,
                    data: activeDataset.map(d => d[`${keyPrefix}${l[2]}x`]),
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    borderDash: [3, 3],
                    pointRadius: 0,
                    fill: 1,
                    backgroundColor: 'rgba(44, 122, 123, 0.45)'
                },
                {
                    label: `${l[3]}x PE 估值線 ${metricSuffix} (${l[2]}x ~ ${l[3]}x 合理偏高)`,
                    data: activeDataset.map(d => d[`${keyPrefix}${l[3]}x`]),
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    borderDash: [3, 3],
                    pointRadius: 0,
                    fill: 2,
                    backgroundColor: 'rgba(47, 133, 90, 0.45)'
                },
                {
                    label: `${l[4]}x PE 估值線 ${metricSuffix} (${l[3]}x ~ ${l[4]}x 昂貴區)`,
                    data: activeDataset.map(d => d[`${keyPrefix}${l[4]}x`]),
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    borderDash: [3, 3],
                    pointRadius: 0,
                    fill: 3,
                    backgroundColor: 'rgba(116, 66, 16, 0.45)'
                },
                {
                    label: `${l[5]}x PE 估值線 ${metricSuffix} (${l[4]}x ~ ${l[5]}x 極度昂貴)`,
                    data: activeDataset.map(d => d[`${keyPrefix}${l[5]}x`]),
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    borderDash: [3, 3],
                    pointRadius: 0,
                    fill: 4,
                    backgroundColor: 'rgba(116, 42, 42, 0.45)'
                },
                {
                    label: `${indexLabel}收盤價 (Index Price)`,
                    data: prices,
                    borderColor: varColor('--accent-cyan'),
                    borderWidth: 2.5,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: varColor('--accent-cyan'),
                    pointHoverBorderColor: '#ffffff',
                    pointHoverBorderWidth: 2,
                    fill: false,
                    yAxisID: 'y'
                }
            ];
        }
        
        currentChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.03)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: {
                                size: 10
                            },
                            callback: function(val, index) {
                                const dateStr = dates[val];
                                if (dateStr && dateStr.endsWith('-06-30')) {
                                    return dateStr.substring(0, 4);
                                }
                                return null;
                            },
                            autoSkip: false
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: {
                                size: 11
                            },
                            callback: function(value) {
                                return value.toLocaleString('en-US');
                            }
                        },
                        title: {
                            display: true,
                            text: `${indexLabel}價格`,
                            color: '#94a3b8',
                            font: {
                                size: 12,
                                weight: '500'
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#e2e8f0',
                            font: {
                                size: 11,
                                family: 'Inter'
                            },
                            padding: 15,
                            usePointStyle: true,
                            boxWidth: 8
                        },
                        filter: function(item) {
                            if (currentMode === 'sd') {
                                return item.text.includes('SD') || item.text.includes('平均') || item.text.includes('收盤價') || item.text.includes('Price');
                            } else {
                                return item.text.includes('PE') || item.text.includes('收盤價') || item.text.includes('Price');
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: '#ffffff',
                        titleFont: {
                            size: 13,
                            weight: 'bold',
                            family: 'Outfit'
                        },
                        bodyColor: '#cbd5e0',
                        bodyFont: {
                            size: 12,
                            family: 'Inter'
                        },
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 10,
                        callbacks: {
                            title: function(context) {
                                return `📅 日期: ${context[0].label}`;
                            },
                            label: function(context) {
                                const datasetLabel = context.dataset.label || '';
                                const value = context.parsed.y;
                                
                                if (datasetLabel.includes('收盤價')) {
                                    const idx = context.dataIndex;
                                    const item = activeDataset[idx];
                                    const peVal = currentMetric === 'trailing' ? item.PE : item.Forward_PE;
                                    const peLabel = currentMetric === 'trailing' ? 'P/E' : 'Fwd P/E';
                                    const peStr = item ? ` (${peLabel}: ${Number(peVal).toFixed(2)}x)` : '';
                                    return `📈 ${datasetLabel}: ${value.toLocaleString('en-US', { minimumFractionDigits: 2 })} ${peStr}`;
                                }
                                
                                if (datasetLabel.includes('估值線')) {
                                    return `▫️ ${datasetLabel.split(' (')[0]}: ${value.toLocaleString('en-US', { maximumFractionDigits: 1 })}`;
                                }
                                
                                return `${datasetLabel}: ${value.toLocaleString('en-US')}`;
                            }
                        }
                    },
                    zoom: {
                        zoom: {
                            wheel: {
                                enabled: true,
                                speed: 0.08
                            },
                            pinch: {
                                enabled: true
                            },
                            mode: 'x',
                            drag: {
                                enabled: false
                            },
                            onZoom: function({chart}) {
                                if (peChart) {
                                    peChart.options.scales.x.min = chart.scales.x.min;
                                    peChart.options.scales.x.max = chart.scales.x.max;
                                    peChart.update('none');
                                }
                            }
                        },
                        pan: {
                            enabled: true,
                            mode: 'x',
                            threshold: 10,
                            onPan: function({chart}) {
                                if (peChart) {
                                    peChart.options.scales.x.min = chart.scales.x.min;
                                    peChart.options.scales.x.max = chart.scales.x.max;
                                    peChart.update('none');
                                }
                            }
                        }
                    }
                }
            }
        });

        // Initialize P/E Trend Chart
        const peCtx = document.getElementById('peTrendChart').getContext('2d');
        const peTrendTitle = currentMetric === 'trailing' ? `${activeIndexName} 歷史本益比 (PE)` : `${activeIndexName} 滾動 12 個月預估本益比 (Rolling 12M Forward PE)`;
        
        peChart = new Chart(peCtx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: peTrendTitle,
                        data: pes,
                        borderColor: '#c084fc', // Premium Purple
                        borderWidth: 2,
                        pointRadius: 0,
                        pointHoverRadius: 5,
                        pointHoverBackgroundColor: '#c084fc',
                        pointHoverBorderColor: '#ffffff',
                        pointHoverBorderWidth: 2,
                        fill: false
                    },
                    {
                        label: `20年均值 (${meanPE.toFixed(2)}x)`,
                        data: Array(dates.length).fill(meanPE),
                        borderColor: 'rgba(255, 255, 255, 0.4)',
                        borderWidth: 1.5,
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        label: `+1 SD (${(meanPE + stdPE).toFixed(2)}x)`,
                        data: Array(dates.length).fill(meanPE + stdPE),
                        borderColor: 'rgba(245, 158, 11, 0.3)',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        label: `-1 SD (${(meanPE - stdPE).toFixed(2)}x)`,
                        data: Array(dates.length).fill(meanPE - stdPE),
                        borderColor: 'rgba(20, 184, 166, 0.3)',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        label: `+2 SD (${(meanPE + 2*stdPE).toFixed(2)}x)`,
                        data: Array(dates.length).fill(meanPE + 2*stdPE),
                        borderColor: 'rgba(239, 68, 68, 0.3)',
                        borderWidth: 1.5,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        label: `-2 SD (${(meanPE - 2*stdPE).toFixed(2)}x)`,
                        data: Array(dates.length).fill(meanPE - 2*stdPE),
                        borderColor: 'rgba(59, 130, 246, 0.3)',
                        borderWidth: 1.5,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.03)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: {
                                size: 10
                            },
                            callback: function(val, index) {
                                const dateStr = dates[val];
                                if (dateStr && dateStr.endsWith('-06-30')) {
                                    return dateStr.substring(0, 4);
                                }
                                return null;
                            },
                            autoSkip: false
                        }
                    },
                    y: {
                        type: 'linear',
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: {
                                size: 11
                            },
                            callback: function(value) {
                                return value.toFixed(1) + 'x';
                            }
                        },
                        title: {
                            display: true,
                            text: '本益比倍數 (P/E Ratio)',
                            color: '#94a3b8',
                            font: {
                                size: 12,
                                weight: '500'
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#e2e8f0',
                            font: {
                                size: 10,
                                family: 'Inter'
                            },
                            padding: 10,
                            usePointStyle: true,
                            boxWidth: 6
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: '#ffffff',
                        titleFont: {
                            size: 13,
                            weight: 'bold',
                            family: 'Outfit'
                        },
                        bodyColor: '#cbd5e0',
                        bodyFont: {
                            size: 12,
                            family: 'Inter'
                        },
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 10,
                        callbacks: {
                            title: function(context) {
                                return `📅 日期: ${context[0].label}`;
                            },
                            label: function(context) {
                                const datasetLabel = context.dataset.label || '';
                                const value = context.parsed.y;
                                if (datasetLabel.includes('本益比') || datasetLabel.includes('PE')) {
                                    return `📊 ${datasetLabel}: ${value.toFixed(2)}x`;
                                }
                                return `▫️ ${datasetLabel.split(' (')[0]}: ${value.toFixed(2)}x`;
                            }
                        }
                    },
                    zoom: {
                        zoom: {
                            wheel: {
                                enabled: true,
                                speed: 0.08
                            },
                            pinch: {
                                enabled: true
                            },
                            mode: 'x',
                            drag: {
                                enabled: false
                            },
                            onZoom: function({chart}) {
                                if (currentChart) {
                                    currentChart.options.scales.x.min = chart.scales.x.min;
                                    currentChart.options.scales.x.max = chart.scales.x.max;
                                    currentChart.update('none');
                                }
                            }
                        },
                        pan: {
                            enabled: true,
                            mode: 'x',
                            threshold: 10,
                            onPan: function({chart}) {
                                if (currentChart) {
                                    currentChart.options.scales.x.min = chart.scales.x.min;
                                    currentChart.options.scales.x.max = chart.scales.x.max;
                                    currentChart.update('none');
                                }
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Helper function to read CSS variable colors
    function varColor(name) {
        return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    }
    
    // --- 6. Event Listeners ---
    btnSD.addEventListener('click', () => {
        btnSD.classList.add('active');
        btnFixed.classList.remove('active');
        currentMode = 'sd';
        updateDashboard(activeIndexName);
    });
    
    btnFixed.addEventListener('click', () => {
        btnFixed.classList.add('active');
        btnSD.classList.remove('active');
        currentMode = 'fixed';
        updateDashboard(activeIndexName);
    });
    
    btnSOX.addEventListener('click', () => {
        btnSOX.classList.add('active');
        btnSPX.classList.remove('active');
        btnIXIC.classList.remove('active');
        btnDJI.classList.remove('active');
        updateDashboard('SOX');
    });
    
    btnSPX.addEventListener('click', () => {
        btnSPX.classList.add('active');
        btnSOX.classList.remove('active');
        btnIXIC.classList.remove('active');
        btnDJI.classList.remove('active');
        updateDashboard('SPX');
    });
    
    btnIXIC.addEventListener('click', () => {
        btnIXIC.classList.add('active');
        btnSOX.classList.remove('active');
        btnSPX.classList.remove('active');
        btnDJI.classList.remove('active');
        updateDashboard('IXIC');
    });
    
    btnDJI.addEventListener('click', () => {
        btnDJI.classList.add('active');
        btnSOX.classList.remove('active');
        btnSPX.classList.remove('active');
        btnIXIC.classList.remove('active');
        updateDashboard('DJI');
    });
    
    btnTrailing.addEventListener('click', () => {
        btnTrailing.classList.add('active');
        btnForward.classList.remove('active');
        currentMetric = 'trailing';
        updateDashboard(activeIndexName);
    });
    
    btnForward.addEventListener('click', () => {
        btnForward.classList.add('active');
        btnTrailing.classList.remove('active');
        currentMetric = 'forward';
        updateDashboard(activeIndexName);
    });
    
    btnResetZoom.addEventListener('click', () => {
        if (currentChart) {
            currentChart.resetZoom();
        }
        if (peChart) {
            peChart.resetZoom();
        }
    });
    
    // Refresh Data click listener
    btnRefreshData.addEventListener('click', () => {
        const isLocalFile = window.location.protocol === 'file:';
        
        if (isLocalFile) {
            alert(
                "💡 提示：本地端數據一鍵更新功能\n\n" +
                "由於瀏覽器的安全限制，直接按兩下 HTML 檔案（file:// 協定）開啟網頁時，無法在背景直接執行您電腦上的 Python 數據更新腳本。\n\n" +
                "若要啟用此按鈕進行一鍵自動更新，請按照以下步驟操作：\n" +
                "1. 在專案目錄下打開終端機，執行命令：python server.py\n" +
                "2. 啟動後在瀏覽器中打開網頁：http://localhost:8000\n" +
                "3. 之後您即可點擊此按鈕進行一鍵自動重新整理！\n\n" +
                "（或者您也可以直接手動在終端機執行 query_all.py, plot_river.py, compile_data.py，然後重新整理本頁面）"
            );
            return;
        }
        
        if (confirm("是否確定從 LSEG Workspace 重新抓取並編譯最新數據？\n這將會執行 query_all.py, plot_river.py 和 compile_data.py，大約需要 30 秒。")) {
            // Show overlay & disable button
            loadingOverlay.classList.add('active');
            btnRefreshData.classList.add('loading');
            btnRefreshData.disabled = true;
            loadingText.textContent = "正在從 LSEG Workspace 重新整理數據...";
            
            fetch('/api/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw err; });
                }
                return response.json();
            })
            .then(data => {
                loadingText.textContent = "數據整理成功！正在重新載入...";
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            })
            .catch(error => {
                console.error("Refresh error:", error);
                loadingOverlay.classList.remove('active');
                btnRefreshData.classList.remove('loading');
                btnRefreshData.disabled = false;
                
                const logMsg = error.logs ? `\n\n詳細執行日誌如下：\n${error.logs}` : '';
                alert(`❌ 數據整理失敗：${error.message || '伺服器執行錯誤'}${logMsg}`);
            });
        }
    });
    
    // Export charts click listener
    btnExportCharts.addEventListener('click', () => {
        const isLocalFile = window.location.protocol === 'file:';
        
        if (isLocalFile) {
            alert(
                "💡 提示：本地端自動產出圖表功能\n\n" +
                "由於瀏覽器的安全限制，直接開啟 HTML 檔案時無法在背景執行 Python 匯出腳本。\n\n" +
                "請按照以下步驟啟用此功能：\n" +
                "1. 在專案目錄下啟動本地端伺服器：python server.py\n" +
                "2. 在瀏覽器打開網頁：http://localhost:8000\n" +
                "3. 點擊此按鈕即可一鍵產出近 5 年估值折線圖並匯出至 OneDrive 目錄！"
            );
            return;
        }
        
        if (confirm("是否確定重新產出並匯出四大指數的「近 5 年估值折線圖」？\n這將在背景重新計算並匯出至 C:\\Users\\User\\OneDrive\\NoWorkLook\\Week\\Week Charts。")) {
            loadingOverlay.classList.add('active');
            btnExportCharts.classList.add('loading');
            btnExportCharts.disabled = true;
            loadingText.textContent = "正在重新計算並產出近 5 年估值折線圖...";
            
            fetch('/api/export-charts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw err; });
                }
                return response.json();
            })
            .then(data => {
                loadingOverlay.classList.remove('active');
                btnExportCharts.classList.remove('loading');
                btnExportCharts.disabled = false;
                
                alert("✅ 估值折線圖導出成功！\n\n所有近 5 年估值折線圖已成功儲存至 OneDrive！\n路徑：C:\\Users\\User\\OneDrive\\NoWorkLook\\Week\\Week Charts");
            })
            .catch(error => {
                console.error("Export error:", error);
                loadingOverlay.classList.remove('active');
                btnExportCharts.classList.remove('loading');
                btnExportCharts.disabled = false;
                
                const logMsg = error.logs ? `\n\n詳細執行日誌如下：\n${error.logs}` : '';
                alert(`❌ 導出失敗：${error.message || '伺服器執行錯誤'}${logMsg}`);
            });
        }
    });
    
    // Initialize dashboard on start with SOX
    updateDashboard('SOX');
});
