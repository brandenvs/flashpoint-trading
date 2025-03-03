from django.shortcuts import render
import services

def fetch_bybit_data():
    btc_ticker = services.bb_btc_orderbook()
    btc_orderbook = services.bb_btc_orderbook()
    volume_24h = services.bb_btc_volume()

    return {
        'btc_ticker': btc_ticker,
        'btc_orderbook': btc_orderbook,
        'volume_24h': volume_24h
    }


def fetch_valr_data():
    btc_ticker = services.vr_btc_ticker()
    btc_orderbook = services.vr_order_book()
    volume_24h = services.vr_btc_volume()

    return {
        'btc_ticker': btc_ticker,
        'btc_orderbook': btc_orderbook,
        'volume_24h': volume_24h
    }


def calculate_lgp(investment_amount):
    bybit_data = fetch_bybit_data()
    valr_data = fetch_valr_data()

    rate_conversion = services.zar_to_dollar(amount=investment_amount)
    zar_to_usd_rate = rate_conversion['rate']

    valr_btc_usd = services.zar_to_dollar(valr_data['btc_ticker'])
    bybit_btc_usd = bybit_data['btc_ticker']
    btc_volume_from_bybit = rate_conversion['converted_amount'] / bybit_data['btc_ticker']

    # Calculate premium and profit potential

    premium = valr_data - bybit_btc_usd
    percentage_premium = (premium / bybit_btc_usd) * 100
    expected_profit_usd = btc_volume_from_bybit * premium
    expected_profit_zar = expected_profit_usd / zar_to_usd_rate

def dashboard(request):
    return render(request, 'dashboard.html')
