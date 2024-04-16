from django import forms

from budget.models import Category, Subcategory, IncomeCategory


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField()


class JoinFamilyForm(forms.Form):
    invite_link = forms.CharField(label='Invite Link')


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']


class SubcategoryForm(forms.ModelForm):
    class Meta:
        model = Subcategory
        fields = ['name', 'category']

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)


class IncomeCategoryForm(forms.ModelForm):
    class Meta:
        model = IncomeCategory
        fields = ['name']
