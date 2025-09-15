from django import forms

class PerformanceDataForm(forms.Form):
    file = forms.FileField(
        label='Загрузите CSV-файл с данными',
        help_text='Формат: username,completed_tasks,quality_score'
    )