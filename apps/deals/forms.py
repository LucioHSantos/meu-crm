from django import forms
from .models import Deal, DealActivity


class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = [
            'title',
            'value',
            'description',
            'stage',
            'priority',
            'contact',
            'assigned_to',
            'expected_close_date',
            'closed_date',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500',
                'placeholder': 'Deal title',
            }),
            'value': forms.NumberInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500',
                'placeholder': '0.00',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500',
                'placeholder': 'Description',
                'rows': 4,
            }),
            'stage': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500',
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500',
            }),
            'contact': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500',
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500',
            }),
            'expected_close_date': forms.DateInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500',
                'type': 'date',
            }),
            'closed_date': forms.DateInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500',
                'type': 'date',
            }),
        }


class DealActivityForm(forms.ModelForm):
    class Meta:
        model = DealActivity
        fields = ['activity_type', 'title', 'description']
        widgets = {
            'activity_type': forms.Select(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500',
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500',
                'placeholder': 'Activity title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500',
                'placeholder': 'Details',
                'rows': 3,
            }),
        }


class DealFilterForm(forms.Form):
    stage = forms.ChoiceField(
        choices=[('', 'All Stages')] + Deal.STAGE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500',
        }),
    )
    assigned_to = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500',
        }),
    )
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + Deal.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500',
        }),
    )

    def __init__(self, *args, users=None, **kwargs):
        super().__init__(*args, **kwargs)
        if users is not None:
            user_choices = [('', 'All Users')] + [(u.id, str(u)) for u in users]
            self.fields['assigned_to'].choices = user_choices
