# Flashpoint Trading Bot

A Django web application that visualizes and executes cryptocurrency arbitrage trades between ByBit and Valr exchanges. The application calculates the Live Gross Premium (LGP) potential, sets up trades, and executes them according to a defined flow.

## Features

- Real-time market data from ByBit and Valr
- Live Gross Premium (LGP) calculation
- Order book analysis and allocation
- Trade simulation and execution
- Trade history tracking
- Responsive dashboard UI

## Flow Diagram

The trading bot follows this process flow:

1. Fetch BTC prices from ByBit and Valr
2. Calculate the Live Gross Premium (LGP)
3. If LGP is >= 1%, proceed with trade analysis
4. Get BTC volume data from both exchanges
5. Determine tradable BTC volume
6. Analyze order books from both exchanges
7. Allocate trade across different price levels
8. Execute trade if profitable spread (>1%) can be maintained
9. Record trade history

## Technical Stack

- **Backend**: Django (Python)
- **Frontend**: Bootstrap 5, JavaScript
- **Data Visualization**: Mermaid.js
- **APIs**: ByBit and Valr Exchange APIs, Exchange Rate API

## Project Structure

```
app/
├── app/                  # Django project settings
│   ├── settings.py       # Project settings
│   ├── urls.py           # Project URL routing
│   ├── wsgi.py           # WSGI configuration
│   └── asgi.py           # ASGI configuration
├── bot/                  # Main application
│   ├── admin.py          # Admin site configuration
│   ├── apps.py           # App configuration
│   ├── models.py         # Database models
│   ├── services.py       # External API services
│   ├── urls.py           # App URL routing
│   ├── views.py          # View controllers
│   ├── migrations/       # Database migrations
│   └── templates/        # HTML templates
│       ├── dashboard.html # Main dashboard
│       └── shared/       # Shared templates
│           └── base.html # Base template
├── static/               # Static files
│   ├── css/
│   │   └── styles.css    # Custom CSS
│   └── js/
│       └── site.js       # Custom JavaScript
└── manage.py             # Django management script
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/flashpoint-trading.git
   cd flashpoint-trading
   ```

2. Set up a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install django requests
   ```

4. Apply migrations:
   ```
   cd app
   python manage.py makemigrations bot
   python manage.py migrate
   ```

5. Run the development server:
   ```
   python manage.py runserver
   ```

6. Access the dashboard at:
   ```
   http://127.0.0.1:8000/dash/
   ```

## Development

### Adding API Keys

For production use, you'll need to add API keys for ByBit and Valr. Update the `services.py` file with your API keys:

```python
# ByBit API credentials
BYBIT_API_KEY = 'your_bybit_api_key'
BYBIT_API_SECRET = 'your_bybit_api_secret'

# Valr API credentials
VALR_API_KEY = 'your_valr_api_key'
VALR_API_SECRET = 'your_valr_api_secret'
```

### Running Tests

```
python manage.py test bot
```

## Security Considerations

- The current implementation uses Django's built-in secret key. For production, generate a new secret key and store it as an environment variable.
- API keys should be stored securely, preferably using environment variables.
- Enable HTTPS in production to protect API keys and trade data.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.