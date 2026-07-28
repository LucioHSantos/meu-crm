from django import forms

from .models import Contact, ContactNote


INPUT_CLASS = 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500'
SELECT_CLASS = 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500'


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = [
            'name',
            'email',
            'phone',
            'company',
            'position',
            'address',
            'notes',
            'status',
            'source',
            'assigned_to',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Contact name',
            }),
            'email': forms.EmailInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'email@example.com',
            }),
            'phone': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': '+1 (555) 000-0000',
            }),
            'company': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Company name',
            }),
            'position': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Job position',
            }),
            'address': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Address',
                'rows': 3,
            }),
            'notes': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Additional notes',
                'rows': 3,
            }),
            'status': forms.Select(attrs={
                'class': SELECT_CLASS,
            }),
            'source': forms.Select(attrs={
                'class': SELECT_CLASS,
            }),
            'assigned_to': forms.Select(attrs={
                'class': SELECT_CLASS,
            }),
        }


class ContactNoteForm(forms.ModelForm):
    class Meta:
        model = ContactNote
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Write a note...',
                'rows': 4,
            }),
        }


class ContactFilterForm(forms.Form):
    name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Search by name...',
        }),
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Contact.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': SELECT_CLASS,
        }),
    )
    source = forms.ChoiceField(
        choices=[('', 'All Sources')] + Contact.SOURCE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': SELECT_CLASS,
        }),
    )
    assigned_to = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={
            'class': SELECT_CLASS,
        }),
    )

    def __init__(self, *args, user_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user_queryset is not None:
            self.fields['assigned_to'].queryset = user_queryset
        else:
            from django.contrib.auth import get_user_model
            self.fields['assigned_to'].queryset = get_user_model().objects.all()
