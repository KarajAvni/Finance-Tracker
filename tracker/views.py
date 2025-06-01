from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import JsonResponse
from .models import Transaction, Category, SavingsGoal
from .forms import TransactionForm, SavingsGoalForm
from django.core.paginator import Paginator
from django.utils import timezone
import csv
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from decimal import Decimal, InvalidOperation

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
            # More robust validation
            name = request.POST.get('name', '').strip()
            target_amount = request.POST.get('target_amount')
            current_amount = request.POST.get('current_amount', '0')
            target_date = request.POST.get('target_date')
            description = request.POST.get('description', '').strip()
            
            # Validate required fields
            if not name:
                messages.error(request, 'Goal name is required.')
                return redirect('savings_goals')
            
            if not target_amount:
                messages.error(request, 'Target amount is required.')
                return redirect('savings_goals')
                
            if not target_date:
                messages.error(request, 'Target date is required.')
                return redirect('savings_goals')
            
            # Convert and validate amounts
            target_amount = float(target_amount)
            current_amount = float(current_amount) if current_amount else 0
            
            if target_amount <= 0:
                messages.error(request, 'Target amount must be greater than 0.')
                return redirect('savings_goals')
                
            if current_amount < 0:
                messages.error(request, 'Current amount cannot be negative.')
                return redirect('savings_goals')
            
            goal = SavingsGoal(
                user=request.user,
                name=name,
                target_amount=target_amount,
                current_amount=current_amount,
                target_date=target_date,
                description=description
            )
            goal.save()
            messages.success(request, f'Savings goal "{goal.name}" created successfully!')
            
        except ValueError:
            messages.error(request, 'Please enter valid amounts.')
        except Exception as e:
            messages.error(request, 'An error occurred while creating the goal. Please try again.')
    
    return redirect('savings_goals')

@login_required
def add_money_to_goal(request):
    if request.method == 'POST':
        try:
            goal_id = request.POST.get('goal_id')
            amount_str = request.POST.get('amount')
            
            # Validate inputs
            if not goal_id:
                messages.error(request, 'Goal ID is missing.')
                return redirect('savings_goals')
                
            if not amount_str:
                messages.error(request, 'Amount is required.')
                return redirect('savings_goals')
            
            # Try to convert to Decimal first (better for money)
            try:
                amount = Decimal(str(amount_str))
            except (InvalidOperation, ValueError):
                messages.error(request, 'Please enter a valid amount.')
                return redirect('savings_goals')
            
            if amount <= 0:
                messages.error(request, 'Amount must be greater than 0.')
                return redirect('savings_goals')
            
            # Get the goal
            try:
                goal = SavingsGoal.objects.get(id=goal_id, user=request.user)
            except SavingsGoal.DoesNotExist:
                messages.error(request, 'Goal not found.')
                return redirect('savings_goals')
            
            # Update the goal
            goal.current_amount += amount
            goal.save()
            
            messages.success(request, f'Added ${amount:.2f} to "{goal.name}"!')
            
        except Exception as e:
            # Log the full error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error adding money to goal: {str(e)}', exc_info=True)
            
            messages.error(request, 'An error occurred while adding money to the goal. Please try again.')
    
    return redirect('savings_goals')
@login_required
def edit_goal(request, goal_id):
    """Edit an existing savings goal"""
    goal = get_object_or_404(SavingsGoal, id=goal_id, user=request.user)
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name', '').strip()
            target_amount = request.POST.get('target_amount')
            current_amount = request.POST.get('current_amount', '0')
            target_date = request.POST.get('target_date')
            description = request.POST.get('description', '').strip()
            
            # Validate required fields
            if not name:
                messages.error(request, 'Goal name is required.')
                return redirect('savings_goals')
            
            if not target_amount:
                messages.error(request, 'Target amount is required.')
                return redirect('savings_goals')
                
            if not target_date:
                messages.error(request, 'Target date is required.')
                return redirect('savings_goals')
            
            # Convert and validate amounts
            target_amount = float(target_amount)
            current_amount = float(current_amount) if current_amount else 0
            
            if target_amount <= 0:
                messages.error(request, 'Target amount must be greater than 0.')
                return redirect('savings_goals')
                
            if current_amount < 0:
                messages.error(request, 'Current amount cannot be negative.')
                return redirect('savings_goals')
            
            # Update goal
            goal.name = name
            goal.target_amount = target_amount
            goal.current_amount = current_amount
            goal.target_date = target_date
            goal.description = description
            goal.save()
            
            messages.success(request, f'Goal "{goal.name}" updated successfully!')
            
        except ValueError:
            messages.error(request, 'Please enter valid amounts.')
        except Exception as e:
            messages.error(request, 'An error occurred while updating the goal.')
    
    return redirect('savings_goals')

@login_required
def get_goal_data(request, goal_id):
    """Get goal data for editing (AJAX endpoint)"""
    try:
        goal = get_object_or_404(SavingsGoal, id=goal_id, user=request.user)
        data = {
            'id': goal.id,
            'name': goal.name,
            'target_amount': str(goal.target_amount),
            'current_amount': str(goal.current_amount),
            'target_date': goal.target_date.strftime('%Y-%m-%d'),
            'description': goal.description,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': 'Goal not found'}, status=404)

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

# Transactions Export
def export_transactions_csv(request):
    transactions = Transaction.objects.filter(user=request.user).select_related('category')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Description', 'Category', 'Type', 'Amount'])
    
    for t in transactions:
        writer.writerow([
            t.date.strftime('%Y-%m-%d'),
            t.description,
            t.category.name,
            t.type,
            f"${t.amount:.2f}"
        ])
    
    return response

def export_transactions_pdf(request):
    transactions = Transaction.objects.filter(user=request.user).select_related('category')
    
    template = get_template('tracker/transactions_pdf.html')
    html = template.render({'transactions': transactions, 'user': request.user})
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="transactions.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF')
    return response

# Savings Goals Export
def export_goals_csv(request):
    goals = SavingsGoal.objects.filter(user=request.user)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="savings_goals.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Target Amount', 'Current Amount', 'Progress', 'Target Date', 'Status'])
    
    for goal in goals:
        status = "Achieved" if goal.progress_percentage >= 100 else "In Progress"
        writer.writerow([
            goal.name,
            f"${goal.target_amount:.2f}",
            f"${goal.current_amount:.2f}",
            f"{goal.progress_percentage:.1f}%",
            goal.target_date.strftime('%Y-%m-%d'),
            status
        ])
    
    return response

def export_goals_pdf(request):
    goals = SavingsGoal.objects.filter(user=request.user)
    
    # Calculate totals in the view
    total_target = sum(g.target_amount for g in goals)
    total_saved = sum(g.current_amount for g in goals)
    
    context = {
        'goals': goals,
        'user': request.user,
        'total_goals': len(goals),
        'total_target': total_target,
        'total_saved': total_saved,
    }
    
    template = get_template('tracker/goals_pdf.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="savings_goals.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF')
    return response