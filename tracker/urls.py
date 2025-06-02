# tracker/urls.py 
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Home page
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-transaction/', views.add_transaction, name='add_transaction'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('goals/', views.savings_goals, name='savings_goals'),
    path('add-goal/', views.add_goal, name='add_goal'),
    path('add-money-to-goal/', views.add_money_to_goal, name='add_money_to_goal'),
    path('edit-goal/<int:goal_id>/', views.edit_goal, name='edit_goal'),
    path('get-goal-data/<int:goal_id>/', views.get_goal_data, name='get_goal_data'),
    path('delete-transaction/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    path('edit-transaction/<int:transaction_id>/', views.edit_transaction, name='edit_transaction'),
    path('get-transaction-data/<int:transaction_id>/', views.get_transaction_data, name='get_transaction_data'),
    path('delete-goal/<int:goal_id>/', views.delete_goal, name='delete_goal'),
    path('transactions/export/csv/', views.export_transactions_csv, name='export_transactions_csv'),
    path('transactions/export/pdf/', views.export_transactions_pdf, name='export_transactions_pdf'),
    path('goals/export/csv/', views.export_goals_csv, name='export_goals_csv'),
    path('goals/export/pdf/', views.export_goals_pdf, name='export_goals_pdf'),
]