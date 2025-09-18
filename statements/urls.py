from django.urls import path
from . import views

app_name = 'statements'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_statement, name='upload'),
    path('add-account/', views.add_account, name='add_account'),
    path('statements/', views.statement_list, name='statement_list'),
    path('statements/<int:statement_id>/', views.statement_detail, name='statement_detail'),
    path('reports/', views.reports, name='reports'),
    path('investments/', views.investment_detail, name='investment_detail'),
    path('account-values/', views.account_values, name='account_values'),
    path('api/transactions/', views.api_transactions, name='api_transactions'),
]
