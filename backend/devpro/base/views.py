from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render
from django.db.models import Count, Sum
from devpro.base.models import Order


# Create your views here.

@login_not_required
def home(request):
    # Aggregate orders by day
    orders_by_day = Order.objects.values('date').annotate(
        order_count=Count('id'),
        total_amount=Sum('total_amount')
    ).order_by('-date')

    context = {
        'orders_by_day': orders_by_day
    }

    return render(request, 'base/home.html', context)
