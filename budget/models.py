import uuid

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)

    class Meta:
        verbose_name = 'Категории'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')

    class Meta:
        verbose_name = 'Подкатегории'
        verbose_name_plural = 'Подкатегории'

    def __str__(self):
        return self.name


class IncomeCategory(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)

    class Meta:
        verbose_name = 'Источник дохода'
        verbose_name_plural = 'Источник дохода'

    def __str__(self):
        return self.name


class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField()
    income_category = models.ForeignKey(IncomeCategory, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Доходы'
        verbose_name_plural = 'Доходы'

    def __str__(self):
        return self.income_category.name


class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()

    class Meta:
        verbose_name = 'Расходы'
        verbose_name_plural = 'Расходы'

    def __str__(self):
        return self.category.name


class Debts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    start_date = models.DateField()
    repayment_period_months = models.IntegerField()
    end_date = models.DateField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, default=0.0)

    class Meta:
        verbose_name = 'Долги'
        verbose_name_plural = 'Долги'

    def calculate_monthly_payment(self):
        total_amount = self.amount + (self.amount * (self.interest_rate / 100))
        monthly_payment = total_amount / self.repayment_period_months
        return monthly_payment

    def is_paid(self):
        return self.end_date <= timezone.now().date() if self.end_date else False

    def __str__(self):
        return f"{self.user.username} - {self.amount} Статус: {'Оплачено' if self.is_paid() else 'Не оплачено'}"


class Family(models.Model):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_families')


class FamilyMember(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    family = models.ForeignKey(Family, on_delete=models.CASCADE)


class FamilyToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    family = models.ForeignKey('Family', on_delete=models.CASCADE)
    is_used = models.BooleanField(default=False)

    def generate_new_token(self):
        self.token = uuid.uuid4()
        self.is_used = False
        self.save()
