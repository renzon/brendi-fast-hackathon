from django.urls import path

from devpro.base import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/query-llm/', views.query_orders_llm, name='query_llm'),
]
