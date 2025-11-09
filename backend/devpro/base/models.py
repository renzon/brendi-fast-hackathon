from django.db import models
from django_min_custom_user.models import MinAbstractUser


class User(MinAbstractUser):
    pass


from django.contrib.postgres.indexes import GinIndex


class Order(models.Model):
    # Identificadores
    order_id = models.CharField(max_length=100, unique=True, db_index=True)
    customer_id = models.CharField(max_length=100, db_index=True)
    customer_name = models.CharField(max_length=255, db_index=True)

    # Datas (separando datetime e date para queries otimizadas)
    created_at = models.DateTimeField(db_index=True)
    date = models.DateField(db_index=True)  # Para agregações por dia

    # Status
    status = models.CharField(max_length=50, db_index=True)

    # Valores financeiros (em centavos no JSON, convertidos para decimal)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # JSON completo para flexibilidade
    raw_data = models.JSONField()

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            GinIndex(fields=['raw_data'], name='orders_raw_data_gin_idx'),
            models.Index(fields=['date', 'status'], name='orders_date_status_idx'),
            models.Index(fields=['customer_id', 'date'], name='orders_customer_date_idx'),
        ]

    def __str__(self):
        return f"Order {self.order_id} - {self.customer_name}"