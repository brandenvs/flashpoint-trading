from django.urls import path
from . import views

urlpatterns = [
    path('dash/', views.dashboard, name='dashboard'),
    path('api/market-data/', views.get_market_data, name='market_data'),
    path('api/simulate-trade/', views.simulate_trade, name='simulate_trade'),
]