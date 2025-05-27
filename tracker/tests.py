from django.test import TestCase
from django.contrib.auth.models import User
from .models import Transaction, Category

# Create your tests here.


class TransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Food',
            type='expense',
            user=self.user
        )
    
    def test_transaction_creation(self):
        transaction = Transaction.objects.create(
            user=self.user,
            amount=50.00,
            description='Grocery shopping',
            category=self.category,
            type='expense'
        )
        self.assertEqual(transaction.amount, 50.00)
        self.assertEqual(str(transaction), 'Grocery shopping - $50.00')