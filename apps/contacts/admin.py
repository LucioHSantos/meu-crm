from django.contrib import admin

from .models import Contact, ContactNote


class ContactNoteInline(admin.TabularInline):
    model = ContactNote
    extra = 0
    readonly_fields = ('author', 'content', 'created_at')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'company', 'status', 'source', 'assigned_to', 'created_at')
    list_filter = ('status', 'source', 'assigned_to')
    search_fields = ('name', 'email', 'phone', 'company')
    inlines = [ContactNoteInline]


@admin.register(ContactNote)
class ContactNoteAdmin(admin.ModelAdmin):
    list_display = ('contact', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content',)
