import json
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any
from django.db import transaction

from devpro.base.models import Order


class OrderLoader:
    """Serviço responsável por carregar pedidos do JSON para o banco"""

    def load_from_file(self, file_path: str) -> Dict[str, int]:
        """Carrega orders do arquivo JSON"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Assume que o JSON é um array ou tem uma chave 'orders'
        orders = data if isinstance(data, list) else data.get('orders', [])

        return self.bulk_create_orders(orders)

    @transaction.atomic
    def bulk_create_orders(self, orders_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Cria múltiplos pedidos em batch (mais eficiente)"""
        orders_to_create = []
        updated_count = 0
        created_count = 0

        for order_data in orders_data:
            order_obj = self._prepare_order(order_data)

            # Verificar se já existe (upsert pattern)
            existing = Order.objects.filter(order_id=order_obj.order_id).first()
            if existing:
                # Atualizar campos
                for field, value in order_obj.__dict__.items():
                    if not field.startswith('_') and field != 'id':
                        setattr(existing, field, value)
                existing.save()
                updated_count += 1
            else:
                orders_to_create.append(order_obj)

        # Bulk create para performance
        if orders_to_create:
            Order.objects.bulk_create(orders_to_create, batch_size=1000)
            created_count = len(orders_to_create)

        return {
            'created': created_count,
            'updated': updated_count,
            'total': created_count + updated_count
        }

    def _prepare_order(self, order_data: Dict[str, Any]) -> Order:
        """Extrai campos principais e prepara objeto Order"""
        created_at = self._parse_datetime(order_data['createdAt']['iso'])

        total_price = self._cents_to_decimal(order_data.get('totalPrice', 0))
        customer = order_data.get('customer', {})
        return Order(
            order_id=order_data.get('id'),
            customer_id=customer.get('_id', ''),
            customer_name=customer.get('name', ''),
            created_at=created_at,
            date=created_at.date(),  # Extrai apenas a data
            status=order_data.get('status', 'pending'),
            total_amount=total_price,
            subtotal_amount=self._cents_to_decimal(order_data.get('subtotal_price', total_price * 100)),
            discount_amount=self._cents_to_decimal(order_data.get('total_discounts', 0)),
            raw_data=order_data  # Mantém JSON completo
        )

    def _cents_to_decimal(self, cents: int) -> Decimal:
        """Converte centavos (int) para Decimal (ex: 5890 -> 58.90)"""
        return Decimal(cents) / 100

    def _parse_datetime(self, date_str: str) -> datetime:
        """Parse flexível de datas"""
        if not date_str:
            return datetime.now()

        # Tenta formatos comuns
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO com microsegundos
            '%Y-%m-%dT%H:%M:%SZ',  # ISO sem microsegundos
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return datetime.now()
