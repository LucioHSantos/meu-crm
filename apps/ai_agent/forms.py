from django import forms
from django.contrib.auth import get_user_model

from .models import AIAgent, KnowledgeBase, KnowledgeDocument, TrainingData

User = get_user_model()

INPUT_CLASS = 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500'
SELECT_CLASS = 'w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500'


class AIAgentForm(forms.ModelForm):
    class Meta:
        model = AIAgent
        fields = [
            'name',
            'description',
            'business_name',
            'business_description',
            'system_prompt',
            'ollama_model',
            'temperature',
            'max_tokens',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Agent name',
            }),
            'description': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Agent description',
                'rows': 3,
            }),
            'business_name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Business name',
            }),
            'business_description': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Business description',
                'rows': 3,
            }),
            'system_prompt': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'System prompt for the AI',
                'rows': 6,
            }),
            'ollama_model': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'e.g. llama3',
            }),
            'temperature': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '0.1',
                'min': '0',
                'max': '2',
            }),
            'max_tokens': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'min': '1',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-yellow-500 bg-gray-700 border-gray-600 rounded focus:ring-yellow-500',
            }),
        }


class KnowledgeBaseForm(forms.ModelForm):
    class Meta:
        model = KnowledgeBase
        fields = [
            'category',
            'question',
            'answer',
            'is_active',
        ]
        widgets = {
            'category': forms.Select(attrs={
                'class': SELECT_CLASS,
            }),
            'question': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Question or topic',
            }),
            'answer': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Answer or information',
                'rows': 5,
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-yellow-500 bg-gray-700 border-gray-600 rounded focus:ring-yellow-500',
            }),
        }


class TrainingDataForm(forms.ModelForm):
    class Meta:
        model = TrainingData
        fields = [
            'input_message',
            'expected_response',
        ]
        widgets = {
            'input_message': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'User message (input)',
                'rows': 4,
            }),
            'expected_response': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Expected AI response',
                'rows': 4,
            }),
        }


class ConversationFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('bot_active', 'Bot Active'),
        ('waiting_human', 'Waiting Human'),
        ('closed', 'Closed'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': SELECT_CLASS,
        }),
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': SELECT_CLASS,
        }),
    )


class KnowledgeBulkForm(forms.Form):
    items = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'One item per line, format: question|answer',
            'rows': 10,
        }),
    )
    category = forms.ChoiceField(
        choices=KnowledgeBase.CATEGORY_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': SELECT_CLASS,
        }),
    )


class KnowledgeDocumentForm(forms.ModelForm):
    class Meta:
        model = KnowledgeDocument
        fields = ['title', 'file', 'category', 'source_url']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Document title (optional)',
            }),
            'file': forms.FileInput(attrs={
                'class': 'w-full text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-yellow-500 file:text-gray-900 file:font-semibold hover:file:bg-yellow-400 cursor-pointer',
            }),
            'category': forms.Select(attrs={
                'class': SELECT_CLASS,
            }),
            'source_url': forms.URLInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Source URL (optional)',
            }),
        }


class KnowledgeURLForm(forms.Form):
    url = forms.URLField(
        required=True,
        widget=forms.URLInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'https://example.com/page-to-learn',
        }),
    )
    category = forms.ChoiceField(
        choices=KnowledgeBase.CATEGORY_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': SELECT_CLASS,
        }),
    )
