from django.contrib import admin

from budget.models import Income, Expense, Category, IncomeCategory, Debts, Subcategory

admin.site.register(Income)
admin.site.register(Expense)
admin.site.register(Category)
admin.site.register(IncomeCategory)
admin.site.register(Debts)
admin.site.register(Subcategory)

