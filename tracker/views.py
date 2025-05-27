from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from .models import Transaction, Category, SavingsGoal
from .forms import TransactionForm, SavingsGoalForm
from django.core.paginator import Paginator
from django.utils import timezone


# Create your views here.

def home(request):
    """Home page - redirects to dashboard if logged in"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

@login_required
def dashboard(request):
    # Calculate totals
    total_income = Transaction.objects.filter(
        user=request.user, type='income'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    total_expenses = Transaction.objects.filter(
        user=request.user, type='expense'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    balance = total_income - total_expenses
    
    # Recent transactions
    recent_transactions = Transaction.objects.filter(user=request.user)[:5]
    
    # Savings goals
    savings_goals = SavingsGoal.objects.filter(user=request.user)
    for goal in savings_goals:
        # Pre-calculate progress as integer for CSS
        goal.progress_width = min(int(goal.progress_percentage), 100)
    
    context = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'recent_transactions': recent_transactions,
        'savings_goals': savings_goals,
    }
    return render(request, 'tracker/dashboard.html', context)

@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'Transaction added successfully!')
            return redirect('dashboard')
    else:
        form = TransactionForm(user=request.user)
    return render(request, 'tracker/add_transaction.html', {'form': form})

@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date', '-created_at')
    
    # Filtering
    transaction_type = request.GET.get('type')
    category_id = request.GET.get('category')
    month = request.GET.get('month')
    
    if transaction_type:
        transactions = transactions.filter(type=transaction_type)
    
    if category_id:
        transactions = transactions.filter(category_id=category_id)
    
    if month:
        try:
            year, month_num = month.split('-')
            transactions = transactions.filter(date__year=year, date__month=month_num)
        except ValueError:
            pass
    
    # Calculate totals for filtered transactions
    total_income = transactions.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    net_amount = total_income - total_expenses
    
    # Pagination
    paginator = Paginator(transactions, 20)  # Show 20 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter dropdown
    categories = Category.objects.filter(user=request.user)
    
    context = {
        'transactions': page_obj,
        'categories': categories,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_amount': net_amount,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    
    return render(request, 'tracker/transactions.html', context)

@login_required
def savings_goals(request):
    goals = SavingsGoal.objects.filter(user=request.user).order_by('-created_at')
    
    # Calculate summary statistics
    active_goals_count = goals.count()
    total_target = goals.aggregate(Sum('target_amount'))['target_amount__sum'] or 0
    total_saved = goals.aggregate(Sum('current_amount'))['current_amount__sum'] or 0
    
    # Add calculated fields to goals
    for goal in goals:
        goal.remaining_amount = goal.target_amount - goal.current_amount
        goal.is_overdue = goal.target_date < timezone.now().date() and goal.progress_percentage < 100
    
    context = {
        'goals': goals,
        'active_goals_count': active_goals_count,
        'total_target': total_target,
        'total_saved': total_saved,
    }
    
    return render(request, 'tracker/goals.html', context)

@login_required
def add_goal(request):
    if request.method == 'POST':
        try:
            goal = SavingsGoal(
                user=request.user,
                name=request.POST.get('name'),
                target_amount=float(request.POST.get('target_amount')),
                current_amount=float(request.POST.get('current_amount', 0)),
                target_date=request.POST.get('target_date'),
                description=request.POST.get('description', '')
            )
            goal.save()
            messages.success(request, f'Savings goal "{goal.name}" created successfully!')
        except (ValueError, TypeError) as e:
            messages.error(request, 'Please check your input and try again.')
    
    return redirect('savings_goals')

@login_required
def add_money_to_goal(request):
    if request.method == 'POST':
        try:
            goal_id = request.POST.get('goal_id')
            amount = float(request.POST.get('amount'))
            
            goal = get_object_or_404(SavingsGoal, id=goal_id, user=request.user)
            goal.current_amount += amount
            goal.save()
            
            messages.success(request, f'Added ${amount:.2f} to "{goal.name}"!')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount entered.')
    
    return redirect('savings_goals')

@login_required
def delete_transaction(request, transaction_id):
    if request.method == 'POST':
        transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully!')
    
    return redirect('transaction_list')

@login_required
def delete_goal(request, goal_id):
    if request.method == 'POST':
        goal = get_object_or_404(SavingsGoal, id=goal_id, user=request.user)
        goal_name = goal.name
        goal.delete()
        messages.success(request, f'Goal "{goal_name}" deleted successfully!')
    
    return redirect('savings_goals')