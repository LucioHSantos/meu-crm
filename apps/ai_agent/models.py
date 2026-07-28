from django.conf import settings
from django.db import models


class AIAgent(models.Model):
    name = models.CharField(max_length=200, default='AI Assistant')
    description = models.TextField(blank=True, default='')
    business_name = models.CharField(max_length=200, blank=True, default='')
    business_description = models.TextField(blank=True, default='')
    system_prompt = models.TextField(
        blank=True,
        default='You are a helpful assistant for a business. Answer questions politely and accurately based on the provided knowledge base.',
    )
    ollama_model = models.CharField(max_length=100, default='llama3')
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=1024)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class KnowledgeBase(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('products', 'Products'),
        ('services', 'Services'),
        ('pricing', 'Pricing'),
        ('faq', 'FAQ'),
        ('policies', 'Policies'),
        ('hours', 'Business Hours'),
        ('contact', 'Contact Info'),
        ('other', 'Other'),
    ]

    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name='knowledge_items')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    question = models.CharField(max_length=500)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'question']

    def __str__(self):
        return f"{self.question[:80]}"


class TrainingData(models.Model):
    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name='training_data')
    input_message = models.TextField()
    expected_response = models.TextField()
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Training: {self.input_message[:60]}"


class Conversation(models.Model):
    STATUS_CHOICES = [
        ('bot_active', 'Bot Active'),
        ('waiting_human', 'Waiting Human'),
        ('closed', 'Closed'),
    ]

    contact = models.ForeignKey(
        'contacts.Contact',
        on_delete=models.CASCADE,
        related_name='conversations',
    )
    agent = models.ForeignKey(AIAgent, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='bot_active')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_conversations',
    )
    unread_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation with {self.contact.name} ({self.get_status_display()})"


class Message(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('bot', 'Bot'),
        ('human_agent', 'Human Agent'),
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender_type = models.CharField(max_length=20, choices=SENDER_CHOICES)
    content = models.TextField()
    whatsapp_message_id = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender_type}: {self.content[:50]}"
