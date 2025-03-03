from django.shortcuts import render
from django.http import JsonResponse
from decimal import Decimal
import bot.services as services
import logging

logger = logging.getLogger(__name__)

def dashboard(request):
    """Render the main dashboard view"""
    return render(request, 'dashboard.html')

def get_market_data(request):
    """API endpoint to get the current market data"""
    try:
        # Get ByBit data
        bybit_data = {
            'btc_ticker': services.bb_btc_ticker(),
            'btc_orderbook': services.bb_btc_orderbook(),
            'volume_24h': services.bb_btc_volume()
        }
        
        # Get Valr data
        valr_data = {
            'btc_ticker': services.vr_btc_ticker(),
            'btc_orderbook': services.vr_order_book(),
            'volume_24h': services.vr_btc_volume()
        }
        
        # Get exchange rate
        exchange_rate = services.get_exchange_rate()
        
        # Calculate LGP (Live Gross Premium)
        valr_btc_usd = services.zar_to_dollar(zar_price=valr_data['btc_ticker'])
        bybit_btc_usd = bybit_data['btc_ticker']
        
        premium = Decimal(str(valr_btc_usd)) - Decimal(str(bybit_btc_usd))
        percentage_premium = (premium / Decimal(str(bybit_btc_usd))) * Decimal('100')
        
        # Determine if premium is suitable for trading (> 1%)
        can_trade = percentage_premium >= 1
        
        # If premium is suitable, calculate tradable BTC
        tradable_btc = None
        order_book_analysis = None
        
        if can_trade:
            tradable_btc = services.calculate_tradable_btc(
                bybit_data['volume_24h'], 
                valr_data['volume_24h']
            )
            
            # Analyze order books to determine if trade is possible
            order_book_analysis = services.analyze_order_books(
                bybit_data['btc_orderbook'],
                valr_data['btc_orderbook'],
                tradable_btc
            )
            
            # Convert Decimal objects in order_book_analysis for JSON serialization
            if order_book_analysis and 'trade_levels' in order_book_analysis:
                serialized_levels = []
                for level in order_book_analysis['trade_levels']:
                    serialized_level = {
                        'valr_price_zar': float(level['valr_price_zar']),
                        'bybit_price_usd': float(level['bybit_price_usd']),
                        'quantity': float(level['quantity']),
                        'spread_percentage': float(level['spread_percentage'])
                    }
                    
                    # Add valr_price_usd if present
                    if 'valr_price_usd' in level:
                        serialized_level['valr_price_usd'] = float(level['valr_price_usd'])
                    else:
                        # If not present, calculate it from ZAR price
                        serialized_level['valr_price_usd'] = serialized_level['valr_price_zar'] / float(exchange_rate)
                        
                    serialized_levels.append(serialized_level)
                
                order_book_analysis['trade_levels'] = serialized_levels
                order_book_analysis['can_execute'] = bool(order_book_analysis['can_execute'])
                order_book_analysis['tradable_volume'] = float(order_book_analysis['tradable_volume'])
        
        return JsonResponse({
            'success': True,
            'data': {
                'bybit_price_usd': float(bybit_btc_usd) if bybit_btc_usd else None,
                'valr_price_zar': float(valr_data['btc_ticker']) if valr_data['btc_ticker'] else None,
                'valr_price_usd': float(valr_btc_usd) if valr_btc_usd else None,
                'exchange_rate': float(exchange_rate) if exchange_rate else None,
                'premium_usd': float(premium) if premium else None,
                'premium_percentage': float(percentage_premium) if percentage_premium else None,
                'can_trade': can_trade,
                'tradable_btc': float(tradable_btc) if tradable_btc else None,
                'order_book_analysis': order_book_analysis,
            }
        })
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def simulate_trade(request):
    """API endpoint to simulate a trade based on current market conditions"""
    try:
        investment_amount = Decimal(request.GET.get('amount', '10000'))  # Default 10,000 ZAR
        
        # Get current market data
        bybit_btc_usd = services.bb_btc_ticker()
        valr_btc_usd = services.vr_btc_ticker()
        exchange_rate = services.get_exchange_rate()
        
        premium = Decimal(str(valr_btc_usd)) - Decimal(str(bybit_btc_usd))
        percentage_premium = (premium / Decimal(str(bybit_btc_usd))) * Decimal('100')

        
        # Check if premium is suitable for trading
        if percentage_premium < 1:
            return JsonResponse({
                'success': False,
                'message': f'Premium too low ({percentage_premium:.2f}%)'
            })
        
        # Calculate amount of BTC to buy on ByBit
        investment_usd = investment_amount / exchange_rate
        btc_amount = investment_usd / bybit_btc_usd
        
        # Calculate expected profit
        sell_value_zar = btc_amount * valr_btc_usd
        expected_profit_zar = sell_value_zar - investment_amount
        expected_profit_percentage = (expected_profit_zar / investment_amount) * 100
        
        return JsonResponse({
            'success': True,
            'simulation': {
                'investment_amount_zar': float(investment_amount),
                'investment_amount_usd': float(investment_usd),
                'btc_amount': float(btc_amount),
                'bybit_buy_price_usd': float(bybit_btc_usd),
                'valr_sell_price_zar': float(valr_btc_usd),
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