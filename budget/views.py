import csv
from datetime import date, timedelta

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import cache_page
from matplotlib import pyplot as plt
from io import BytesIO
import base64
from .forms import CSVUploadForm, CategoryForm, SubcategoryForm, IncomeCategoryForm
from .models import Income, Expense, Category, Debts, Family, FamilyMember, Subcategory, IncomeCategory, FamilyToken


# -----------------Расходы----------------

@login_required()
@cache_page(60 * 5)
def expense_list(request):
    """
        Функция представления для отображения списка расходов текущего пользователя или члена семьи.
        Если пользователь является членом семьи, отображаются только расходы за текущий месяц и год.
        В противном случае отображаются все расходы пользователя.
    """
    current_user = request.user
    family_member = FamilyMember.objects.filter(user=current_user).first()
    if not family_member:
        expenses = Expense.objects.filter(user=current_user).order_by('date')
    else:
        today = date.today()
        current_month = today.month
        current_year = today.year
        expenses = Expense.objects.filter(user__familymember=family_member, date__month=current_month,
                                          date__year=current_year).order_by('date')
    categories = Category.objects.all()
    total_amount = expenses.aggregate(total_amount=Sum('amount'))['total_amount'] or 0

    return render(request, 'budget/expense_list.html',
                  {'expenses': expenses, 'categories': categories, 'total_amount': total_amount})


@login_required()
def add_expense(request):
    """
        Функция представления для добавления нового расхода.
        Если выбрана категория, динамически загружаются подкатегории на основе выбранной категории.
    """
    current_user = request.user
    if request.method == 'POST':
        amount = request.POST.get('amount')
        category_id = request.POST.get('category')
        subcategory_id = request.POST.get('subcategory')
        date = request.POST.get('date')

        if not amount or not category_id or not subcategory_id or not date:
            messages.warning(request, 'Пожалуйста, заполните все поля.')
            return redirect('add_expense')

        category = Category.objects.get(id=category_id)
        subcategory = Subcategory.objects.get(id=subcategory_id)
        user = request.user

        Expense.objects.create(user=user, amount=amount, category=category, subcategory=subcategory, date=date)
        messages.success(request, 'Расход успешно добавлен!')

        return redirect('expense_list')

    categories = Category.objects.filter(user=current_user)
    subcategories = Subcategory.objects.none()

    selected_category_id = request.GET.get('category')
    if selected_category_id:
        selected_category = Category.objects.get(id=selected_category_id)
        subcategories = selected_category.subcategories.all()

    return render(request, 'budget/add_expense.html',
                  {'categories': categories, 'subcategories': subcategories,
                   'selected_category_id': selected_category_id})


@login_required()
@cache_page(60 * 5)
def category_list(request):
    """
        Функция представления для отображения списка категорий расходов текущего пользователя.
    """
    categories = Category.objects.filter(user=request.user)
    return render(request, 'budget/category_list.html', {'categories': categories})


@login_required()
def add_category(request):
    """
       Функция представления для добавления новой категории расходов.
    """
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, 'Категория успешно добавлена!')
            return redirect('add_expense')
        else:
            messages.warning(request, 'Пожалуйста, заполните все поля.')
    else:
        form = CategoryForm()
    return render(request, 'budget/add_category.html', {'form': form})


@login_required()
def delete_category(request, category_id):
    """
        Функция представления для удаления категории расходов.
    """
    category = get_object_or_404(Category, id=category_id)
    if category.user == request.user:
        category.delete()
        messages.success(request, 'Категория удалена!')
        return redirect('category_list')

    return render(request, 'budget/delete_category.html', {'category': category})


@login_required()
@cache_page(60 * 5)
def subcategory_list(request):
    """
        Функция представления для отображения списка подкатегорий на основе категорий расходов текущего пользователя.
    """
    categories = Category.objects.filter(user=request.user)
    subcategories = Subcategory.objects.filter(category__in=categories)
    return render(request, 'budget/subcategory_list.html', {'subcategories': subcategories})


@login_required()
def add_subcategory(request):
    """
        Функция представления для добавления новой подкатегории.
    """
    if request.method == 'POST':
        form = SubcategoryForm(request.user, request.POST)
        if form.is_valid():
            subcategory = form.save(commit=False)
            subcategory.user = request.user
            subcategory.save()
            messages.success(request, 'Подкатегория успешно добавлена!')
            return redirect('add_expense')
        else:
            messages.warning(request, 'Пожалуйста, заполните все поля.')
    else:
        form = SubcategoryForm(request.user)
    return render(request, 'budget/add_subcategory.html', {'form': form})


@login_required()
def delete_subcategory(request, subcategory_id):
    """
        Функция представления для удаления подкатегории.
    """
    subcategory = get_object_or_404(Subcategory, pk=subcategory_id)
    if subcategory.category.user == request.user:
        subcategory.delete()
        messages.success(request, 'Подкатегория удалена!')
    return redirect('subcategory_list')


@login_required()
def filter_expenses(request):
    """
        Функция представления для фильтрации расходов по начальной и конечной датам.
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    current_user = request.user
    family_member = FamilyMember.objects.filter(user=current_user).first()
    if not family_member:
        expenses = Expense.objects.filter(user=current_user)
        total_amount = expenses.aggregate(total_amount=Sum('amount'))['total_amount'] or 0
    else:
        family_members = FamilyMember.objects.filter(family=family_member.family)
        expenses = Expense.objects.filter(user__familymember__in=family_members)
        if start_date and end_date:
            expenses = expenses.filter(date__range=[start_date, end_date])
        total_amount = expenses.aggregate(total_amount=Sum('amount'))['total_amount'] or 0

    return render(request, 'budget/expense_list.html',
                  {'expenses': expenses, 'total_amount': total_amount})


@login_required()
def edit_expense(request, expense_id):
    """
        Функция представления для редактирования существующего расхода.
        Если выбрана категория, динамически загружаются подкатегории на основе выбранной категории.
    """
    expense = get_object_or_404(Expense, pk=expense_id)
    categories = Category.objects.all()
    subcategories = Subcategory.objects.none()

    if request.method == 'POST':
        category_id = request.POST['category']
        subcategory_id = request.POST['subcategory']
        amount = request.POST['amount']
        date = request.POST['date']

        category = Category.objects.get(id=category_id)
        subcategory = Subcategory.objects.get(id=subcategory_id)

        expense.category = category
        expense.subcategory = subcategory
        expense.amount = amount
        expense.date = date
        expense.save()

        messages.success(request, 'Расход успешно изменен!')
        return redirect('expense_list')

    selected_category_id = request.GET.get('category')
    if selected_category_id:
        selected_category = Category.objects.get(id=selected_category_id)
        subcategories = selected_category.subcategories.all()

    return render(request, 'budget/edit_expense.html', {'expense': expense,
                                                        'categories': categories, 'subcategories': subcategories,
                                                        'selected_category_id': expense.category_id})


@login_required()
def delete_expense(request, expense_id):
    """
        Функция представления для удаления расхода.
    """
    expense = get_object_or_404(Expense, pk=expense_id)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Расход успешно удален!')

    return redirect('expense_list')


@login_required()
def export_expenses_csv(request):
    """
        Функция представления для экспорта расходов в CSV файл.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'First name', 'Category', 'Subcategory', 'Amount'])

    expenses = Expense.objects.filter(user=request.user)
    for expense in expenses:
        writer.writerow([expense.date, expense.user.first_name,
                         expense.category.name, expense.subcategory, expense.amount])

    return response


@login_required()
def import_expenses_csv(request):
    """
        Функция представления для импорта расходов из CSV файла.
    """
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            expenses_file = request.FILES['csv_file']
            decoded_file = expenses_file.read().decode('utf-8').splitlines()
            reader = csv.reader(decoded_file)
            for row in reader:
                date, category_name, subcategory, amount = row
                category, created = Category.objects.get_or_create(name=category_name)
                Expense.objects.create(user=request.user, date=date, category=category,
                                       subcategory=subcategory, amount=amount)
            return render(request, 'success.html', {'message': 'Data imported successfully!'})
    else:
        form = CSVUploadForm()

    return render(request, 'budget/import_expenses.html', {'form': form})


# -----------------Доходы----------------

@login_required()
@cache_page(60 * 5)
def income_list(request):
    """
        Функция представления для отображения списка доходов текущего пользователя или члена семьи.
    """
    selected_month = request.GET.get('month')
    selected_year = request.GET.get('year')
    today = date.today()
    current_month = today.month if not selected_month else int(selected_month)
    current_year = today.year if not selected_year else int(selected_year)
    years_list = [str(year) for year in range(2020, 2031)]
    current_user = request.user
    family_member = FamilyMember.objects.filter(user=current_user).first()
    if not family_member:
        incomes = Income.objects.filter(user=current_user).order_by('date')
    else:
        family_members = FamilyMember.objects.filter(family=family_member.family)
        incomes = Income.objects.filter(user__familymember__in=family_members, date__month=current_month,
                                        date__year=current_year).order_by('date')

    return render(request, 'budget/income_list.html',
                  {'incomes': incomes, 'years_list': years_list, 'selected_month': current_month,
                   'selected_year': current_year})


@login_required()
def add_income(request):
    """
        Функция представления для добавления нового дохода.
    """
    if request.method == 'POST':
        amount = request.POST['amount']
        description = request.POST['description']
        income_category_id = request.POST['income_category']
        date = request.POST['date']
        income_category = IncomeCategory.objects.get(id=income_category_id)
        user = request.user
        Income.objects.create(user=user, amount=amount, description=description, income_category=income_category,
                              date=date)
        messages.success(request, 'Доход успешно добавлен.')
        return redirect('income_list')
    income_category = IncomeCategory.objects.filter(user=request.user)
    return render(request, 'budget/add_income.html', {'income_category': income_category})


@login_required()
@cache_page(60 * 5)
def income_category_list(request):
    """
        Функция представления для отображения списка категорий доходов текущего пользователя.
    """
    income_categories = IncomeCategory.objects.filter(user=request.user)
    return render(request, 'budget/income_category_list.html', {'income_categories': income_categories})


@login_required()
def add_income_category(request):
    """
        Функция представления для добавления новой категории доходов.
    """
    if request.method == 'POST':
        form = IncomeCategoryForm(request.POST)
        if form.is_valid():
            new_category = form.save(commit=False)
            new_category.user = request.user
            new_category.save()
            messages.success(request, 'Источник дохода успешно добавлен!')
            return redirect('add_income')
        else:
            messages.warning(request, 'Пожалуйста, заполните поле!')
    else:
        form = IncomeCategoryForm()
    return render(request, 'budget/add_income_category.html', {'form': form})


@login_required()
def delete_income_category(request, category_id):
    """
        Функция представления для удаления категории доходов.
    """
    category = get_object_or_404(IncomeCategory, pk=category_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Категория дохода успешно удалена.')
        return redirect('income_category_list')
    return render(request, 'budget/delete_income_category.html', {'category': category})


@login_required()
def edit_income(request, income_id):
    """
        Функция представления для редактирования существующего дохода.
    """
    income = get_object_or_404(Income, pk=income_id)
    income_category = IncomeCategory.objects.filter(user=request.user)
    if request.method == 'POST':
        income.amount = request.POST['amount']
        income.description = request.POST['description']
        income.income_category_id = request.POST['income_category']
        income.date = request.POST['date']
        income.save()
        messages.success(request, 'Доход изменен успешно!')
        return redirect('income_list')

    return render(request, 'budget/edit_income.html',
                  {'income': income, 'income_category': income_category})


@login_required()
def delete_income(request, income_id):
    """
        Функция представления для удаления дохода.
    """
    income = get_object_or_404(Income, pk=income_id)
    if request.method == 'POST':
        income.delete()
        messages.success(request, 'Доход успешно удален!')
    return redirect('income_list')


# ---------------------Долги-----------------------------

@login_required()
@cache_page(60 * 5)
def debts_list(request):
    """
        Функция представления для отображения списка долгов текущего пользователя или члена семьи.
    """
    current_user = request.user
    family_member = FamilyMember.objects.filter(user=current_user).first()
    if not family_member:
        debts = Debts.objects.filter(user=current_user)
    else:
        family_members = FamilyMember.objects.filter(family=family_member.family)
        debts = Debts.objects.filter(user__familymember__in=family_members)

    return render(request, 'budget/debts_list.html', {'debts': debts})


@login_required()
def add_debts(request):
    """
        Функция представления для добавления нового долга.
    """
    if request.method == 'POST':
        user = request.user
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        repayment_period_months = int(request.POST.get('repayment_period_months'))
        interest_rate = float(request.POST.get('interest_rate'))
        start_date = date.fromisoformat(start_date)
        end_date = start_date + timedelta(days=repayment_period_months * 30)
        Debts.objects.create(
            user=user,
            amount=amount,
            description=description,
            start_date=start_date,
            repayment_period_months=repayment_period_months,
            end_date=end_date,
            interest_rate=interest_rate
        )
        messages.success(request, 'Долг успешно добавлен!')
        return redirect('debts_list')

    return render(request, 'budget/add_debts.html')


@login_required()
def delete_debts(request, debts_id):
    """
        Функция представления для удаления долга.
    """
    debts = get_object_or_404(Debts, pk=debts_id)
    if request.method == 'POST':
        debts.delete()
        messages.success(request, 'Долг успешно удален!')

    return redirect('debts_list')


# ------------------Отчеты------------------------

@login_required()
@cache_page(60 * 5)
def income_expense_report(request):
    """
        Функция отчета о доходах и расходах.
    """
    selected_month = request.GET.get('month')
    selected_year = request.GET.get('year')

    if selected_month:
        selected_month = int(selected_month)
    else:
        selected_month = date.today().month

    if not selected_year:
        selected_year = date.today().year

    incomes = Income.objects.filter(date__month=selected_month, date__year=selected_year)
    expenses = Expense.objects.filter(date__month=selected_month, date__year=selected_year)
    years_list = [year for year in range(2020, timezone.now().year + 1)]

    if not incomes.exists() and not expenses.exists():
        no_data_message = f"Нет данных о расходах и доходах за выбранный месяц {selected_month} и год {selected_year}."
        return render(request, 'budget/income_expense_report.html', {'no_data_message': no_data_message,
                                                                     'years_list': years_list,
                                                                     'selected_month': selected_month,
                                                                     'selected_year': selected_year})

    total_income = incomes.aggregate(total_income=Sum('amount'))['total_income'] or 0
    total_expense = expenses.aggregate(total_expense=Sum('amount'))['total_expense'] or 0
    income_balance = total_income - total_expense
    top_expenses = expenses.values('category__name').annotate(total_amount=Sum('amount')).order_by('-total_amount')[:5]

    fig, axes = plt.subplots(1, 2, figsize=(15, 8))
    labels = ['Расходы', 'Доходы']
    amounts = [total_expense, total_income]
    colors = ['lightblue', 'lightcoral']
    explode = (0.1, 0)
    axes[0].pie(amounts, labels=labels, autopct='%1.1f%%', colors=colors, explode=explode, shadow=True, startangle=140)
    axes[0].set_title('Доходы и расходы')

    axes[0].text(-1.5, 1.5, f'Общий доход: {total_income}', horizontalalignment='center',
                 verticalalignment='center', fontsize=12)
    axes[0].text(-1.5, 1.3, f'Расходы: {total_expense}', horizontalalignment='center',
                 verticalalignment='center', fontsize=12)
    axes[0].text(-1.5, 1.1, f'Остаток: {income_balance}', horizontalalignment='center',
                 verticalalignment='center', fontsize=12)

    categories = [expense['category__name'] for expense in top_expenses]
    top_amounts = [expense['total_amount'] for expense in top_expenses]
    axes[1].pie(top_amounts, labels=categories, autopct='%1.1f%%', shadow=True, startangle=140)
    axes[1].set_title('Расход по категориям')

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    graphic = base64.b64encode(image_png).decode()

    plt.close()

    return render(request, 'budget/income_expense_report.html', {'graphic': graphic,
                                                                 'years_list': years_list,
                                                                 'selected_month': selected_month,
                                                                 'selected_year': selected_year})


@login_required()
def select_category_report(request):
    """
        Функция выбора отчета по категории.
    """
    years_list = [year for year in range(2020, timezone.now().year + 1)]

    if request.method == 'POST':
        category_id = request.POST.get('category')
        selected_month = request.POST.get('month')
        selected_year = request.POST.get('year')

        if category_id and selected_month and selected_year:
            return redirect('category_expense_report', category_id=category_id, month=selected_month,
                            year=selected_year)
        else:
            return HttpResponse('Не все параметры выбраны. Вернитесь назад и выберите все параметры.')

    user_categories = Category.objects.filter(user=request.user)
    return render(request, 'budget/select_category_report.html',
                  {'user_categories': user_categories, 'years_list': years_list})


@login_required()
@cache_page(60 * 5)
def category_expense_report(request, category_id, year=None, month=None):
    """
        Функция отчета о расходах по категории.
    """
    category = get_object_or_404(Category, id=category_id)
    expenses = Expense.objects.filter(category=category)
    if year:
        expenses = expenses.filter(date__year=year)
    if month:
        expenses = expenses.filter(date__month=month)
    if not expenses.exists():
        period = f'{date(year, month, 1).strftime("%B")} {year}' if year and month else 'current period'
        message = f"No expenses for category '{category.name}' in {period}."
        return render(request, 'budget/category_expense_report.html', {'message': message})

    subcategory_expenses = expenses.values('subcategory__name').annotate(total_expense=Sum('amount'))
    subcategories_list = [expense['subcategory__name'] for expense in subcategory_expenses]
    sub_expenses_list = [expense['total_expense'] for expense in subcategory_expenses]

    fig, ax = plt.subplots()
    ax.pie(sub_expenses_list, labels=subcategories_list, autopct='%1.1f%%')
    ax.set_title(f'Расходы по категории: {category.name}')

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    graphic = base64.b64encode(image_png).decode()

    plt.close()

    return render(request, 'budget/category_expense_report.html', {
        'graphic': graphic,
        'category': category,
        'year': year,
        'month': month,
    })


# -----------------Семейный аккаунт----------------

@login_required()
def dashboard(request):
    """
        Функция представления для отображения панели управления (dashboard).
    """
    user_family_member = FamilyMember.objects.filter(user=request.user).first()
    family = user_family_member.family if user_family_member else None
    family_members = FamilyMember.objects.filter(family=family) if family else []

    family_token = FamilyToken.objects.filter(family=family, is_used=False).first() if family else None

    return render(request, 'budget/dashboard.html', {
        'user': request.user,
        'family': family,
        'family_members': family_members,
        'family_token': family_token,
    })


@login_required()
def create_family(request):
    """
        Функция представления для создания семьи.
    """
    if request.method == 'POST':
        family_name = request.POST.get('family_name')
        current_user = request.user
        family = Family.objects.create(name=family_name, created_by=current_user)
        FamilyToken.objects.create(family=family)
        FamilyMember.objects.create(user=request.user, family=family)
        messages.success(request, 'Семья успешно создана!')

        return redirect('dashboard')

    return render(request, 'budget/create_family.html')


@login_required()
def join_family(request):
    """
        Функция представления для присоединения к семье.
    """
    if request.method == 'POST':
        token = request.POST.get('family_token')
        try:
            family_token = FamilyToken.objects.get(token=token, is_used=False)
            family = family_token.family
            family_token.is_used = True
            family_token.save()
            FamilyMember.objects.create(user=request.user, family=family)
            messages.success(request, 'Вы успешно присоединились к семье!')

            family_token.generate_new_token()

            return redirect('dashboard')

        except FamilyToken.DoesNotExist:
            messages.error(request, 'Неверный токен для присоединения к семье.')

            return redirect('join_family')

    return render(request, 'budget/join_family.html')


@login_required()
def leave_family(request):
    """
        Функция представления для выхода из семьи.
    """
    if request.method == 'POST':
        FamilyMember.objects.filter(user=request.user).delete()
        messages.success(request, 'Вы покинули семью.')

        return redirect('dashboard')

    return render(request, 'budget/leave_family.html')


# ------------------------Курсы валют-----------------------------

@login_required()
def get_currency_rates(request):
    url = 'https://www.nbrb.by/api/exrates/rates?periodicity=0'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        rates = {rate['Cur_Name']: rate['Cur_OfficialRate'] for rate in data}
        return rates
    else:
        return {}


@login_required()
def currency_rates(request):
    rates = get_currency_rates(request)
    return render(request, 'budget/currency.html', {'currency_rates': rates})


@cache_page(60 * 5)
def currency_converter(request):
    if request.method == 'POST':
        from_currency = request.POST.get('from_currency')

        amount = float(request.POST.get('amount', 2))

        rates = get_currency_rates(request)
        if from_currency in rates:
            from_rate = rates[from_currency]

            converted_amount = amount * from_rate
            result = f"{converted_amount:.2f} Белорусских рублей."

        currencies = rates.keys()
        return render(request, 'budget/currency.html', {'currencies': currencies, 'result': result})
    else:
        rates = get_currency_rates()
        currencies = rates.keys()
        return render(request, 'budget/currency.html', {'currencies': currencies})