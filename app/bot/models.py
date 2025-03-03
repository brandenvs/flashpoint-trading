from django.db import models
from decimal import Decimal

class Trade(models.Model):
    """Model to store trade history"""
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
        (CANCELLED, 'Cancelled'),
    ]
    
    # Trade details
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    investment_amount_zar = models.DecimalField(max_digits=20, decimal_places=2)
    btc_volume = models.DecimalField(max_digits=20, decimal_places=8)
    bybit_price_usd = models.DecimalField(max_digits=20, decimal_places=2)
    valr_price_zar = models.DecimalField(max_digits=20, decimal_places=2)
    usd_zar_rate = models.DecimalField(max_digits=10, decimal_places=4)
    premium_percentage = models.DecimalField(max_digits=10, decimal_places=2)
    profit_zar = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    
    # Additional details for debugging/audit
    bybit_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    valr_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Trade #{self.id} - {self.btc_volume} BTC - {self.status}"
    
    @property
    def profit_percentage(self):
        """Calculate profit percentage"""
        if self.profit_zar and self.investment_amount_zar:
            return (self.profit_zar / self.investment_amount_zar) * Decimal('100')
        return None


class TradeLevel(models.Model):
    """Model to store details of each price level in a trade"""
    trade = models.ForeignKey(Trade, on_delete=models.CASCADE, related_name='levels')
    bybit_price_usd = models.DecimalField(max_digits=20, decimal_places=2)
    valr_price_zar = models.DecimalField(max_digits=20, decimal_places=2)
    btc_volume = models.DecimalField(max_digits=20, decimal_places=8)
    spread_percentage = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"Level for Trade #{self.trade.id} - {self.btc_volume} BTC at {self.spread_percentage}% spread"