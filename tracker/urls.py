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
    path('delete-goal/<int:goal_id>/', views.delete_goal, name='delete_goal'),
]