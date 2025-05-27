from django.contrib import admin
from .models import Category, Transaction, SavingsGoal

# Register your models here.


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'user']
    list_filter = ['type', 'user']
    search_fields = ['name']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['description', 'amount', 'type', 'category', 'user', 'date']
    list_filter = ['type', 'category', 'date', 'user']
    search_fields = ['description']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']

@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ['name', 'current_amount', 'target_amount', 'progress_percentage', 'target_date', 'user']
    list_filter = ['target_date', 'user']
    search_fields = ['name']
    readonly_fields = ['progress_percentage']
    
    def progress_percentage(self, obj):
        return f"{obj.progress_percentage:.1f}%"
    progress_percentage.short_description = 'Progress'