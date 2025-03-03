"""
Views module for the bot application.
This module contains views for rendering the dashboard and API endpoints
for fetching market data and simulating trades.
"""

from django.shortcuts import render
from django.http import JsonResponse
from decimal import Decimal
import logging
import bot.services as services

logger = logging.getLogger(__name__)

def dashboard(request):
    """Render the main dashboard view"""
    return render(request, 'dashboard.html')

def get_market_data(request):
    """
    API endpoint to get the current market data from both exchanges.
    
    Returns JSON with:
    - Exchange rates
    - Current prices (BTC in USD and ZAR)
    - Premium calculation
    - Order book analysis (if premium is sufficient)
    """
    try:
        # Get exchange rate
        exchange_rate = services.get_exchange_rate()
        if not exchange_rate:
            return JsonResponse({
                'success': False,
                'error': 'Failed to get exchange rate'
            })
        
        # Get ByBit data
        bybit_btc_usd = services.bb_btc_ticker()
        bybit_orderbook = services.bb_btc_orderbook()
        bybit_volume = services.bb_btc_volume()
        
        if not bybit_btc_usd:
            return JsonResponse({
                'success': False,
                'error': 'Failed to get ByBit BTC price'
            })
        
        # Get Valr data
        valr_btc_zar = services.vr_btc_ticker()
        valr_orderbook = services.vr_order_book()
        valr_volume = services.vr_btc_volume()
        
        if not valr_btc_zar:
            return JsonResponse({
                'success': False,
                'error': 'Failed to get Valr BTC price'
            })
        
        # Calculate Live Gross Premium (LGP)
        valr_btc_usd = services.zar_to_dollar(valr_btc_zar)
        premium = valr_btc_usd - bybit_btc_usd
        percentage_premium = (premium / bybit_btc_usd) * 100
        
        # Determine if premium is suitable for trading (≥ 1%)
        can_trade = percentage_premium >= 1
        
        # Initialize optional fields
        tradable_btc = None
        order_book_analysis = None
        
        # If premium is suitable, calculate tradable BTC and analyze order books
        if can_trade and bybit_volume and valr_volume:
            tradable_btc = services.calculate_tradable_btc(bybit_volume, valr_volume)
            
            if tradable_btc > 0 and bybit_orderbook and valr_orderbook:
                order_book_analysis = services.analyze_order_books(
                    bybit_orderbook,
                    valr_orderbook,
                    tradable_btc
                )
        
        # Prepare response data
        market_data = {
            'bybit_price_usd': float(bybit_btc_usd) if bybit_btc_usd else None,
            'valr_price_zar': float(valr_btc_zar) if valr_btc_zar else None,
            'valr_price_usd': float(valr_btc_usd) if valr_btc_usd else None,
            'exchange_rate': float(exchange_rate) if exchange_rate else None,
            'premium_usd': float(premium) if premium is not None else None,
            'premium_percentage': float(percentage_premium) if percentage_premium is not None else None,
            'can_trade': can_trade,
            'tradable_btc': float(tradable_btc) if tradable_btc else None,
        }
        
        # Add order book analysis if available
        if order_book_analysis:
            # Convert Decimal objects to float for JSON serialization
            if 'trade_levels' in order_book_analysis:
                serialized_levels = []
                for level in order_book_analysis['trade_levels']:
                    serialized_level = {
                        'valr_price_zar': float(level['valr_price_zar']),
                        'bybit_price_usd': float(level['bybit_price_usd']),
                        'quantity': float(level['quantity']),
                        'spread_percentage': float(level['spread_percentage']),
                        'valr_price_usd': float(level['valr_price_usd'])
                    }
                    serialized_levels.append(serialized_level)
                
                order_book_analysis['trade_levels'] = serialized_levels
                order_book_analysis['can_execute'] = bool(order_book_analysis['can_execute'])
                order_book_analysis['tradable_volume'] = float(order_book_analysis['tradable_volume'])
            
            market_data['order_book_analysis'] = order_book_analysis
        
        return JsonResponse({
            'success': True,
            'data': market_data
        })
    
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def simulate_trade(request):
    """
    API endpoint to simulate a trade based on current market conditions.
    
    Takes an investment amount and calculates potential profit based on
    current market conditions.
    """
    try:
        # Get investment amount from request, default to 10,000 ZAR
        investment_amount = Decimal(request.GET.get('amount', '10000'))
        
        # Get current market data
        bybit_price = services.bb_btc_ticker()
        valr_price = services.vr_btc_ticker()
        exchange_rate = services.get_exchange_rate()
        
        if not all([bybit_price, valr_price, exchange_rate]):
            return JsonResponse({
                'success': False,
                'message': 'Failed to get required market data'
            })
        
        # Convert valr price to USD for comparison
        valr_price_usd = valr_price / exchange_rate
        
        # Calculate premium
        premium = valr_price_usd - bybit_price
        percentage_premium = (premium / bybit_price) * 100
        
        # Check if premium is suitable for trading
        if percentage_premium < 1:
            return JsonResponse({
                'success': False,
                'message': f'Premium too low ({percentage_premium:.2f}%)'
            })
        
        # Calculate amount of BTC to buy on ByBit
        investment_usd = investment_amount / exchange_rate
        btc_amount = investment_usd / bybit_price
        
        # Calculate expected profit
        sell_value_zar = btc_amount * valr_price
        expected_profit_zar = sell_value_zar - investment_amount
        expected_profit_percentage = (expected_profit_zar / investment_amount) * 100
        
        return JsonResponse({
            'success': True,
            'simulation': {
                'investment_amount_zar': float(investment_amount),
                'investment_amount_usd': float(investment_usd),
                'btc_amount': float(btc_amount),
                'bybit_buy_price_usd': float(bybit_price),
                'valr_sell_price_zar': float(valr_price),
                'expected_profit_zar': float(expected_profit_zar),
                'expected_profit_percentage': float(expected_profit_percentage),
                'exchange_rate': float(exchange_rate)
            }
        })
    
    except Exception as e:
        logger.error(f"Error simulating trade: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })