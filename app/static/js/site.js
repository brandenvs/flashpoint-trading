// Flashpoint Trading Bot JavaScript

/**
 * Utility Functions
 */

// Get CSRF token from the meta tag
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Format numbers for display
function formatNumber(number, decimals = 2) {
    if (number === null || number === undefined) return 'N/A';
    return number.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

// Format currency for display
function formatCurrency(amount, currency = 'USD', decimals = 2) {
    if (amount === null || amount === undefined) return 'N/A';
    return amount.toLocaleString('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

// Format percentage for display
function formatPercentage(percentage, decimals = 2) {
    if (percentage === null || percentage === undefined) return 'N/A';
    return percentage.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }) + '%';
}

// Format BTC amount for display
function formatBTC(amount, decimals = 8) {
    if (amount === null || amount === undefined) return 'N/A';
    return amount.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }) + ' BTC';
}

/**
 * Market Data Functions
 */

// Update market data
function updateMarketData() {
    fetch('/api/market-data/')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                displayMarketData(result.data);
                updateLastUpdatedTime();
            } else {
                console.error('Error fetching market data:', result.error);
                showErrorNotification('Failed to update market data');
            }
        })
        .catch(error => {
            console.error('Error fetching market data:', error);
            showErrorNotification('Network error while updating market data');
        });
}

// Display market data on the dashboard
function displayMarketData(data) {
    // Update prices
    document.getElementById('bybit-price').textContent = formatCurrency(data.bybit_price_usd);
    document.getElementById('valr-price-zar').textContent = formatCurrency(data.valr_price_zar, 'ZAR');
    document.getElementById('valr-price-usd').textContent = formatCurrency(data.valr_price_usd);
    document.getElementById('exchange-rate').textContent = formatNumber(data.exchange_rate);

    // Update premium
    document.getElementById('premium-usd').textContent = formatCurrency(data.premium_usd);
    const premiumElement = document.getElementById('premium-percentage');
    premiumElement.textContent = formatPercentage(data.premium_percentage);

    // Update premium status indicator
    updatePremiumStatus(data);

    // Update trading section if applicable
    updateTradingSection(data);
}

// Update premium status indicator
function updatePremiumStatus(data) {
    const premiumStatusElement = document.getElementById('premium-status');

    if (data.premium_percentage >= 1) {
        premiumStatusElement.textContent = 'TRADING OPPORTUNITY';
        premiumStatusElement.className = 'badge bg-success';
    } else {
        premiumStatusElement.textContent = 'NO OPPORTUNITY';
        premiumStatusElement.className = 'badge bg-danger';
    }
}

// Update trading section based on premium status
function updateTradingSection(data) {
    const tradingSection = document.getElementById('trading-section');
    const orderBookAnalysisSection = document.getElementById('order-book-analysis');

    if (data.premium_percentage >= 1) {
        // Show trading section
        tradingSection.classList.remove('d-none');

        // Update tradable volume
        document.getElementById('tradable-btc').textContent = formatBTC(data.tradable_btc);

        // Update order book analysis if available
        if (data.order_book_analysis &&
            data.order_book_analysis.trade_levels &&
            Array.isArray(data.order_book_analysis.trade_levels) &&
            data.order_book_analysis.trade_levels.length > 0) {

            displayOrderBookAnalysis(data.order_book_analysis);
            orderBookAnalysisSection.classList.remove('d-none');
        } else {
            console.log("No order book analysis data available or empty trade levels");
            orderBookAnalysisSection.classList.add('d-none');
        }
    } else {
        // Hide trading section
        tradingSection.classList.add('d-none');
    }
}

// Display order book analysis
function displayOrderBookAnalysis(analysisData) {
    const tradeTableBody = document.getElementById('trade-levels-body');
    tradeTableBody.innerHTML = '';

    analysisData.trade_levels.forEach(level => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatCurrency(level.valr_price_zar, 'ZAR')}</td>
            <td>${formatCurrency(level.valr_price_usd)}</td>
            <td>${formatCurrency(level.bybit_price_usd)}</td>
            <td>${formatBTC(level.quantity)}</td>
            <td>${formatPercentage(level.spread_percentage)}</td>
        `;
        tradeTableBody.appendChild(row);
    });
}

// Update last updated timestamp
function updateLastUpdatedTime() {
    document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
}

/**
 * Trade Simulation Functions
 */

// Simulate trade
function simulateTrade() {
    const amountInput = document.getElementById('investment-amount');
    const amount = amountInput.value;

    if (!amount || isNaN(amount) || parseFloat(amount) <= 0) {
        alert('Please enter a valid investment amount');
        return;
    }

    fetch(`/api/simulate-trade/?amount=${amount}`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                displaySimulationResults(result.simulation);
            } else {
                handleSimulationError(result);
            }
        })
        .catch(error => {
            console.error('Error simulating trade:', error);
            alert('Error simulating trade: ' + error);
        });
}

// Display simulation results
function displaySimulationResults(simulation) {
    document.getElementById('sim-investment-zar').textContent = formatCurrency(simulation.investment_amount_zar, 'ZAR');
    document.getElementById('sim-investment-usd').textContent = formatCurrency(simulation.investment_amount_usd);
    document.getElementById('sim-btc-amount').textContent = formatBTC(simulation.btc_amount);
    document.getElementById('sim-bybit-price').textContent = formatCurrency(simulation.bybit_buy_price_usd);
    document.getElementById('sim-valr-price').textContent = formatCurrency(simulation.valr_sell_price_zar, 'ZAR');
    document.getElementById('sim-profit-zar').textContent = formatCurrency(simulation.expected_profit_zar, 'ZAR');
    document.getElementById('sim-profit-percentage').textContent = formatPercentage(simulation.expected_profit_percentage);

    // Show simulation results
    document.getElementById('simulation-results').classList.remove('d-none');
}

// Handle simulation error
function handleSimulationError(result) {
    if (result.message) {
        alert(result.message);
    } else {
        alert('Error simulating trade: ' + result.error);
    }
}

/**
 * Notification Functions
 */

// Show error notification
function showErrorNotification(message) {
    // Implementation can be improved with a toast notification system
    console.error(message);
}

/**
 * Initialize the application
 */
document.addEventListener('DOMContentLoaded', function () {
    // Set up event listeners
    const simulateButton = document.getElementById('simulate-button');
    if (simulateButton) {
        simulateButton.addEventListener('click', simulateTrade);
    }

    // Set up refresh button
    const refreshButton = document.querySelector('button[onclick="updateMarketData()"]');
    if (refreshButton) {
        refreshButton.onclick = function (e) {
            e.preventDefault();
            updateMarketData();
        };
    }

    // Initial market data update
    updateMarketData();

    // Set interval to update market data every 30 seconds
    setInterval(updateMarketData, 30000);
});