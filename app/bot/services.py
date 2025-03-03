import requests
import json
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# ByBit API endpoints
BYBIT_BASE_URL = "https://api.bybit.com"
BYBIT_TICKER_ENDPOINT = "/v5/market/tickers"
BYBIT_ORDERBOOK_ENDPOINT = "/v5/market/orderbook"
BYBIT_KLINE_ENDPOINT = "/v5/market/kline"

# Valr API endpoints
VALR_BASE_URL = "https://api.valr.com"
VALR_TICKER_ENDPOINT = "/v1/public/BTCZAR/marketsummary"
VALR_ORDERBOOK_ENDPOINT = "/v1/public/BTCZAR/orderbook"
VALR_VOLUME_ENDPOINT = "/v1/public/BTCZAR/marketsummary"

# Exchange rate API
EXCHANGE_RATE_API = "https://open.er-api.com/v6/latest/USD"

def handle_request_errors(func):
    """Decorator to handle request errors with more detailed logging"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.RequestException as e:
            logger.error(f"API request failed in {func.__name__}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in {func.__name__}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            return None
    return wrapper

@handle_request_errors
def get_exchange_rate():
    """Get USD to ZAR exchange rate"""
    response = requests.get(EXCHANGE_RATE_API)
    data = response.json()
    return Decimal(str(data['rates']['ZAR']))

@handle_request_errors
def zar_to_dollar(amount=None, zar_price=None):
    """Convert ZAR to USD"""
    exchange_rate = get_exchange_rate()
    
    if amount is not None:
        converted_amount = Decimal(str(amount)) / exchange_rate
        return {
            'rate': exchange_rate,
            'converted_amount': converted_amount
        }
    
    if zar_price is not None:
        converted_price = Decimal(str(zar_price)) / exchange_rate
        return converted_price
    
    return None

# ByBit API functions
@handle_request_errors
def bb_btc_ticker():
    """Get BTC ticker from ByBit"""
    params = {
        'category': 'spot',
        'symbol': 'BTCUSDT'
    }
    response = requests.get(BYBIT_BASE_URL + BYBIT_TICKER_ENDPOINT, params=params)
    data = response.json()
    
    if data['retCode'] == 0 and data['result']['list']:
        return Decimal(data['result']['list'][0]['lastPrice'])
    
    return None

@handle_request_errors
def bb_btc_orderbook():
    """Get BTC orderbook from ByBit"""
    params = {
        'category': 'spot',
        'symbol': 'BTCUSDT',
        'limit': 50
    }
    response = requests.get(BYBIT_BASE_URL + BYBIT_ORDERBOOK_ENDPOINT, params=params)
    data = response.json()
    
    if data['retCode'] == 0:
        return {
            'bids': [(Decimal(bid[0]), Decimal(bid[1])) for bid in data['result']['b']],
            'asks': [(Decimal(ask[0]), Decimal(ask[1])) for ask in data['result']['a']]
        }
    
    return None

@handle_request_errors
def bb_btc_volume():
    """Get BTC 24h volume from ByBit"""
    params = {
        'category': 'spot',
        'symbol': 'BTCUSDT',
        'interval': 'D'
    }
    response = requests.get(BYBIT_BASE_URL + BYBIT_KLINE_ENDPOINT, params=params)
    data = response.json()
    
    if data['retCode'] == 0 and data['result']['list']:
        # Volume is in the 6th position of each kline data
        return Decimal(data['result']['list'][0][5])
    
    return None

# Valr API functions
@handle_request_errors
def vr_btc_ticker():
    """Get BTC ticker from Valr"""
    response = requests.get(VALR_BASE_URL + VALR_TICKER_ENDPOINT)
    data = response.json()
    
    return Decimal(data['lastTradedPrice'])

@handle_request_errors
def vr_order_book():
    """Get BTC orderbook from Valr"""
    response = requests.get(VALR_BASE_URL + VALR_ORDERBOOK_ENDPOINT)
    data = response.json()
    
    return {
        'bids': [(Decimal(bid['price']), Decimal(bid['quantity'])) for bid in data['Bids']],
        'asks': [(Decimal(ask['price']), Decimal(ask['quantity'])) for ask in data['Asks']]
    }

@handle_request_errors
def vr_btc_volume():
    """Get BTC 24h volume from Valr"""
    response = requests.get(VALR_BASE_URL + VALR_VOLUME_ENDPOINT)
    data = response.json()

    # Sum up the volume from trade history
    volume = Decimal(data['baseVolume'])

    return volume

def calculate_tradable_btc(bybit_volume, valr_volume):
    """Calculate the tradable BTC volume"""
    # Using the minimum of both exchanges' volumes as a conservative approach
    # Typically we'd only want to trade up to some percentage of the available liquidity
    return min(bybit_volume, valr_volume) * Decimal('0.1')  # 10% of available liquidity

def analyze_order_books(bybit_orderbook, valr_orderbook, target_btc_volume):
    """Analyze order books to determine if trade is possible"""
    # Check if orderbooks are available
    if not bybit_orderbook or not valr_orderbook:
        logger.warning("Order books are not available")
        return {
            'can_execute': False,
            'tradable_volume': Decimal('0'),
            'trade_levels': []
        }
    
    try:
        # Convert VALR orderbook prices from ZAR to USD for comparison
        usd_zar_rate = get_exchange_rate()
        
        if not usd_zar_rate:
            logger.warning("Exchange rate not available")
            return {
                'can_execute': False,
                'tradable_volume': Decimal('0'),
                'trade_levels': []
            }
        
        # Convert Valr asks to USD (these are the prices we buy at)
        valr_asks_usd = [(ask_price / usd_zar_rate, quantity) for ask_price, quantity in valr_orderbook['asks']]
        
        # ByBit bids are the prices we sell at
        bybit_bids = bybit_orderbook['bids']
        
        # Check if we can execute the full trade with a profitable spread
        cumulative_btc = Decimal('0')
        trade_levels = []
        
        # Only add levels with a profitable spread (>= 1%)
        for i in range(min(len(valr_asks_usd), len(bybit_bids))):
            valr_price, valr_qty = valr_asks_usd[i]
            bybit_price, bybit_qty = bybit_bids[i]
            
            # Calculate spread - valr_price is already in USD at this point
            spread = bybit_price - valr_price
            spread_percentage = (spread / valr_price) * 100
            
            # Only include levels with a profitable spread (>= 1%)
            if spread_percentage >= 1:
                trade_qty = min(valr_qty, bybit_qty)
                
                if cumulative_btc + trade_qty >= target_btc_volume:
                    # Adjust trade_qty to meet target_btc_volume exactly
                    trade_qty = target_btc_volume - cumulative_btc
                    
                    trade_levels.append({
                        'valr_price_zar': valr_price * usd_zar_rate,
                        'valr_price_usd': valr_price,  # Add USD price for comparison
                        'bybit_price_usd': bybit_price,
                        'quantity': trade_qty,
                        'spread_percentage': spread_percentage
                    })
                    
                    cumulative_btc += trade_qty
                    break
                else:
                    trade_levels.append({
                        'valr_price_zar': valr_price * usd_zar_rate,
                        'valr_price_usd': valr_price,  # Add USD price for comparison
                        'bybit_price_usd': bybit_price,
                        'quantity': trade_qty,
                        'spread_percentage': spread_percentage
                    })
                    
                    cumulative_btc += trade_qty
            else:
                # If we hit a level with insufficient spread, stop
                break
        
        return {
            'can_execute': cumulative_btc > Decimal('0'),
            'tradable_volume': cumulative_btc,
            'trade_levels': trade_levels
        }
    except Exception as e:
        logger.error(f"Error analyzing order books: {e}")
        return {
            'can_execute': False,
            'tradable_volume': Decimal('0'),
            'trade_levels': []
        }