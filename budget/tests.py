"""
    Тесты для представлений и функционала приложения бюджета.

    Тесты представления и функционала, предоставляемого приложением бюджета,
    включая управление расходами, управление доходами, управление долгами, отчеты и управление семьей.
"""
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from budget.views import *


class ExpenseViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass1234')
        self.client.login(username='testuser', password='testpass1234')
        self.category = Category.objects.create(name='Test Category', user=self.user)
        self.subcategory = Subcategory.objects.create(name='Test Subcategory', category=self.category)

    def test_expense_list(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('expense_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'budget/expense_list.html')

    def test_add_expense(self):
        response = self.client.post(reverse('add_expense'), {
            'amount': 100,
            'category': self.category.id,
            'subcategory': self.subcategory.id,
            'date': '2024-04-17',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('expense_list'), status_code=302, target_status_code=200)
        self.assertTrue(Expense.objects.filter(user=self.user, amount=100).exists())

    def test_category_list(self):
        response = self.client.get(reverse('category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'budget/category_list.html')

    def test_add_category(self):
        response = self.client.post(reverse('add_category'), {
            'name': 'New Category'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('add_expense'), status_code=302, target_status_code=200)
        self.assertTrue(Category.objects.filter(user=self.user, name='New Category').exists())

    def test_delete_category(self):
        category = Category.objects.create(name='Delete Category', user=self.user)
        response = self.client.post(reverse('delete_category', kwargs={'category_id': category.id}))
        self.assertRedirects(response, reverse('category_list'), status_code=302, target_status_code=200)
        self.assertFalse(Category.objects.filter(id=category.id).exists())

    def test_add_subcategory(self):
        response = self.client.post(reverse('add_subcategory'), {
            'name': 'New Subcategory', 'category': self.category.id
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Subcategory.objects.filter(name='New Subcategory').exists())

    def test_delete_subcategory(self):
        response = self.client.post(reverse('delete_subcategory', kwargs={'subcategory_id': self.subcategory.id}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Subcategory.objects.filter(id=self.subcategory.id).exists())

    def test_edit_expense(self):
        self.client.force_login(self.user)
        expense = Expense.objects.create(user=self.user, amount=100, category=self.category,
                                         subcategory=self.subcategory, date='2024-04-17')
        response = self.client.post(reverse('edit_expense', kwargs={'expense_id': expense.id}), {
            'category': self.category.id,
            'subcategory': self.subcategory.id,
            'amount': 200,
            'date': '2024-04-17',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Expense.objects.get(id=expense.id).amount, 200)

    def test_delete_expense(self):
        expense = Expense.objects.create(user=self.user, amount=100, category=self.category,
                                         subcategory=self.subcategory, date='2024-04-17')
        response = self.client.post(reverse('delete_expense', kwargs={'expense_id': expense.id}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('expense_list'), status_code=302, target_status_code=200)
        self.assertFalse(Expense.objects.filter(id=expense.id).exists())

class IncomeViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass1234')
        self.client.login(username='testuser', password='testpass1234')
        self.income_category = IncomeCategory.objects.create(name='Test Income Category', user=self.user)
        self.income = Income.objects.create(user=self.user, amount=200, description='Test income',
                                            income_category=self.income_category, date='2024-04-17')

    def test_income_list(self):
        response = self.client.get(reverse('income_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'budget/income_list.html')

    def test_add_income(self):
        response = self.client.post(reverse('add_income'), {
            'amount': 300,
            'description': 'New income',
            'income_category': self.income_category.id,
            'date': '2024-04-17'
        })
        self.assertEqual(response.status_code, 302)
        added_income = Income.objects.filter(amount=300, user=self.user)
        self.assertTrue(added_income.exists())

    def test_income_category_list(self):
        response = self.client.get(reverse('income_category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'budget/income_category_list.html')

    def test_add_income_category(self):
        response = self.client.post(reverse('add_income_category'), {
            'name': 'New Income Category'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(IncomeCategory.objects.filter(name='Test Income Category').exists())

    def test_delete_income_category(self):
        response = self.client.post(reverse('delete_income_category', kwargs={'category_id': self.income_category.id}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('income_category_list'), status_code=302, target_status_code=200)
        self.assertFalse(IncomeCategory.objects.filter(id=self.income_category.id).exists())

    def test_edit_income(self):
        response = self.client.post(reverse('edit_income', kwargs={'income_id': self.income.id}), {
            'amount': 300,
            'description': 'Edited income',
            'income_category': self.income_category.id,
            'date': '2024-04-17'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('income_list'), status_code=302, target_status_code=200)
        self.assertTrue(Income.objects.filter(amount=300, description='Edited income').exists())

    def test_delete_income(self):
        response = self.client.post(reverse('delete_income', kwargs={'income_id': self.income.id}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('income_list'), status_code=302, target_status_code=200)
        self.assertFalse(Income.objects.filter(id=self.income.id).exists())


class DebtsViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass1234')
        self.client.login(username='testuser', password='testpass1234')
        self.debt = Debts.objects.create(
            user=self.user,
            amount=500,
            description='Test debt',
            start_date=date(2023, 4, 10),
            repayment_period_months=6,
            end_date=date(2023, 10, 10),
            interest_rate=5.0
        )

    def test_debts_list(self):
        response = self.client.get(reverse('debts_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'budget/debts_list.html')

    def test_add_debts(self):
        response = self.client.post(reverse('add_debts'), {
            'amount': 300,
            'description': 'New debt',
            'start_date': '2024-04-20',
            'repayment_period_months': 12,
            'interest_rate': 4.5
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('debts_list'), status_code=302, target_status_code=200)
        self.assertTrue(Debts.objects.filter(description='New debt').exists())

    def test_delete_debts(self):
        response = self.client.post(reverse('delete_debts', kwargs={'debts_id': self.debt.id}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('debts_list'), status_code=302, target_status_code=200)
        self.assertFalse(Debts.objects.filter(id=self.debt.id).exists())


class ReportTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass1234')
        self.client.login(username='testuser', password='testpass1234')
        self.category = Category.objects.create(user=self.user, name='TestCategory')
        self.subcategory = Subcategory.objects.create(name='TestSubcategory', category=self.category)
        self.expense = Expense.objects.create(user=self.user, amount=100, category=self.category,
                                              subcategory=self.subcategory, date=date.today())
        self.income_category = IncomeCategory.objects.create(user=self.user, name='TestIncomeCategory')
        self.income = Income.objects.create(user=self.user, amount=200, description='Test Income', date=date.today(),
                                            income_category=self.income_category)

    def test_income_expense_report(self):
        response = self.client.get(reverse('income_expense_report'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'budget/income_expense_report.html')

    def test_select_category_report(self):
        response = self.client.get(reverse('select_category_report'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'budget/select_category_report.html')

    def test_category_expense_report(self):
        response = self.client.get(reverse('category_expense_report',
                                           kwargs={'category_id': self.category.id, 'month': 4, 'year': 2024}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'budget/category_expense_report.html')


class FamilyManagementTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='testuser1', email='test@example.com', password='testpass1234')
        self.user2 = User.objects.create_user(username='testuser2', email='test@example.com', password='testpass1234')
        self.client.login(username='testuser1', password='testpass1234')

    def test_create_family(self):
        response = self.client.post(reverse('create_family'), {
            'family_name': 'Test Family'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Family.objects.filter(name='Test Family', created_by=self.user1).exists())
        self.assertTrue(FamilyToken.objects.filter(family__name='Test Family').exists())
        self.assertTrue(FamilyMember.objects.filter(user=self.user1, family__name='Test Family').exists())

    def test_join_family_with_valid_token(self):
        self.client.login(username='testuser2', password='testpass1234')
        family = Family.objects.create(name='Test Family', created_by=self.user1)
        family_token = FamilyToken.objects.create(family=family)
        response = self.client.post(reverse('join_family'), {
            'family_token': family_token.token
        })
        self.assertEqual(response.status_code, 302)
        family_member = FamilyMember.objects.filter(user=self.user2, family=family_token.family).first()
        self.assertIsNotNone(family_member)
        self.assertFalse(family_token.is_used)

    def test_join_family_with_invalid_token(self):
        self.client.login(username='testuser2', password='testpass1234')
        family = Family.objects.create(name='Test Family', created_by=self.user1)
        invalid_token = FamilyToken.objects.create(family=family, is_used=True)
        response = self.client.post(reverse('join_family'), {
            'family_token': invalid_token.token
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('join_family'))
        family_member = FamilyMember.objects.filter(user=self.user2, family=family).first()
        self.assertIsNone(family_member)

    def test_leave_family(self):
        self.client.login(username='testuser2', password='testpass1234')
        family = Family.objects.create(name='Тестовая семья', created_by=self.user1)
        FamilyMember.objects.create(user=self.user2, family=family)
        response = self.client.post(reverse('leave_family'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(FamilyMember.objects.filter(user=self.user1, family=family).exists())
        self.assertFalse(FamilyMember.objects.filter(user=self.user2, family=family).exists())
