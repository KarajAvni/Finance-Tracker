from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Category

@receiver(post_save, sender=User)
def create_default_categories(sender, instance, created, **kwargs):
    """
    Create default categories when a new user is created
    """
    if created:  # Only for newly created users
        default_categories = [
            ('Salary', 'income'),
            ('Food & Dining', 'expense'),
            ('Transportation', 'expense'),
            ('Shopping', 'expense'),
            ('Entertainment', 'expense'),
            ('Bills & Utilities', 'expense'),
            ('Healthcare', 'expense'),
            ('Education', 'expense'),
            ('Business Income', 'income'),
            ('Investment Income', 'income'),
            ('Freelance Income', 'income'),
            ('Rental Income', 'income'),
            ('Savings', 'expense'),
            ('Insurance', 'expense'),
            ('Gifts & Donations', 'expense'),
            ('Other Income', 'income'),
            ('Other Expense', 'expense')
        ]
        
        for category_name, category_type in default_categories:
            Category.objects.create(name=category_name, type=category_type, user=instance)
        
        print(f"Created default categories for user: {instance.username}")