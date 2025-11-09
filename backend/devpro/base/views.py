import json

from django.contrib.auth.decorators import login_not_required
from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Count, Sum
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from openai import OpenAI
from django.conf import settings

from devpro.base.models import Order


# Create your views here.

@login_not_required
def home(request):
    # Aggregate orders by day
    orders_by_day = list(Order.objects.values('date').annotate(
        order_count=Count('id'),
        total_amount=Sum('total_amount')
    ).order_by('-date'))

    context = {
        'orders_by_day': orders_by_day
    }

    return render(request, 'base/home.html', context)


client = OpenAI(api_key=settings.OPEN_AI_API_KEY)


@login_not_required
@require_http_methods(["POST"])
@csrf_exempt
def query_orders_llm(request):
    try:
        data = json.loads(request.body)
        user_query = data.get('query', '')

        if not user_query:
            return JsonResponse({'error': 'Query não pode estar vazia'}, status=400)

        # Buscar dados relevantes do banco
        orders_summary = get_orders_context()

        # Chamar a LLM

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": f"""Você é um assistente de análise de dados de pedidos de restaurante.
                    Use os seguintes dados para responder às perguntas do usuário:

                    {orders_summary}

                    Responda de forma clara e objetiva em português.
                    Se necessário, forneça números específicos e insights."""
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ],
            temperature=0.7,
            max_tokens=500
        )

        answer = response.choices[0].message.content

        return JsonResponse({
            'success': True,
            'answer': answer
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def get_orders_context():
    """Gera um resumo dos dados de pedidos para contexto da LLM. Foca nos dados dos últimos 7 dias."""

    # Total de pedidos
    total_orders = Order.objects.count()

    # Faturamento total
    total_revenue = Order.objects.aggregate(
        total=Sum('total_amount')
    )['total']

    # Pedidos por dia (últimos 30 dias)
    orders_by_day = list(Order.objects.values('date').annotate(
        order_count=Count('id'),
        total_amount=Sum('total_amount')
    ).order_by('-date')[:30])

    # Pedidos por status
    orders_by_status = list(Order.objects.values('status').annotate(
        count=Count('id')
    ))

    # Top clientes
    top_customers = list(Order.objects.values('customer_name').annotate(
        order_count=Count('id'),
        total_spent=Sum('total_amount')
    ).order_by('-total_spent')[:10])

    # Ticket médio
    avg_ticket = Order.objects.aggregate(
        avg=Sum('total_amount')
    )['avg'] / total_orders if total_orders > 0 else 0

    context = f"""
    RESUMO DOS DADOS:

    Total de Pedidos: {total_orders}
    Faturamento Total: R$ {total_revenue:.2f}
    Ticket Médio: R$ {avg_ticket:.2f}

    PEDIDOS POR DIA (Últimos 30 dias):
    {json.dumps(orders_by_day, indent=2, default=str)}

    PEDIDOS POR STATUS:
    {json.dumps(orders_by_status, indent=2)}

    TOP 5 CLIENTES:
    {json.dumps(top_customers, indent=2, default=str)}
    """
    return context
