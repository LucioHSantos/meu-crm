from django.contrib import admin

from .models import AIAgent, Conversation, KnowledgeBase, Message, TrainingData


@admin.register(AIAgent)
class AIAgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_name', 'is_active', 'ollama_model')
    list_filter = ('is_active',)
    search_fields = ('name', 'business_name')


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'is_active', 'agent')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'status', 'assigned_to', 'unread_count', 'created_at')
    list_filter = ('status',)
    search_fields = ('contact__name', 'contact__phone')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('short_content', 'conversation', 'sender_type', 'created_at')
    list_filter = ('sender_type',)
    search_fields = ('content',)

    @admin.display(description='Content')
    def short_content(self, obj):
        return obj.content[:50]


@admin.register(TrainingData)
class TrainingDataAdmin(admin.ModelAdmin):
    list_display = ('short_input', 'agent', 'created_at')
    search_fields = ('input_message', 'expected_response')

    @admin.display(description='Input')
    def short_input(self, obj):
        return obj.input_message[:50]
