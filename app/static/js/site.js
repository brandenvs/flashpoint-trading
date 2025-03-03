// Flashpoint Trading Bot JavaScript

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

// Update market data
function updateMarketData() {
    fetch('/api/market-data/')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const data = result.data;

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
                const premiumStatusElement = document.getElementById('premium-status');
                if (data.premium_percentage >= 1) {
                    premiumStatusElement.textContent = 'TRADING OPPORTUNITY';
                    premiumStatusElement.className = 'badge bg-success';

                    // Show trading section
                    document.getElementById('trading-section').classList.remove('d-none');

                    // Update tradable volume
                    document.getElementById('tradable-btc').textContent = formatBTC(data.tradable_btc);

                    // Update order book analysis if available
                    if (data.order_book_analysis && data.order_book_analysis.trade_levels &&
                        Array.isArray(data.order_book_analysis.trade_levels) &&
                        data.order_book_analysis.trade_levels.length > 0) {

                        console.log("Order book analysis data:", data.order_book_analysis);

                        const tradeTableBody = document.getElementById('trade-levels-body');
                        tradeTableBody.innerHTML = '';

                        data.order_book_analysis.trade_levels.forEach(level => {
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

                        document.getElementById('order-book-analysis').classList.remove('d-none');
                    } else {
                        console.log("No order book analysis data available or empty trade levels");
                        document.getElementById('order-book-analysis').classList.add('d-none');
                    }
                } else {
                    premiumStatusElement.textContent = 'NO OPPORTUNITY';
                    premiumStatusElement.className = 'badge bg-danger';

                    // Hide trading section
                    document.getElementById('trading-section').classList.add('d-none');
                }

                // Show last updated time
                document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
            } else {
                console.error('Error fetching market data:', result.error);
            }
        })
        .catch(error => {
            console.error('Error fetching market data:', error);
        });
}

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
                const simulation = result.simulation;

                // Update simulation results
                document.getElementById('sim-investment-zar').textContent = formatCurrency(simulation.investment_amount_zar, 'ZAR');
                document.getElementById('sim-investment-usd').textContent = formatCurrency(simulation.investment_amount_usd);
                document.getElementById('sim-btc-amount').textContent = formatBTC(simulation.btc_amount);
                document.getElementById('sim-bybit-price').textContent = formatCurrency(simulation.bybit_buy_price_usd);
                document.getElementById('sim-valr-price').textContent = formatCurrency(simulation.valr_sell_price_zar, 'ZAR');
                document.getElementById('sim-profit-zar').textContent = formatCurrency(simulation.expected_profit_zar, 'ZAR');
                document.getElementById('sim-profit-percentage').textContent = formatPercentage(simulation.expected_profit_percentage);

                // Show simulation results
                document.getElementById('simulation-results').classList.remove('d-none');
            } else {
                if (result.message) {
                    alert(result.message);
                } else {
                    alert('Error simulating trade: ' + result.error);
                }
            }
        })
        .catch(error => {
            console.error('Error simulating trade:', error);
            alert('Error simulating trade: ' + error);
        });
}

// Event listener for the simulate button
document.addEventListener('DOMContentLoaded', function () {
    const simulateButton = document.getElementById('simulate-button');
    if (simulateButton) {
        simulateButton.addEventListener('click', simulateTrade);
    }

    // Initial market data update
    updateMarketData();

    // Set interval to update market data every 30 seconds
    setInterval(updateMarketData, 30000);
});