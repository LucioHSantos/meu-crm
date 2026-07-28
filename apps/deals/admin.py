from django.contrib import admin
from .models import Deal, DealActivity


class DealActivityInline(admin.TabularInline):
    model = DealActivity
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('title', 'value', 'stage', 'priority', 'contact', 'assigned_to', 'expected_close_date', 'created_at')
    list_filter = ('stage', 'priority', 'assigned_to')
    search_fields = ('title', 'description')
    inlines = [DealActivityInline]


@admin.register(DealActivity)
class DealActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'activity_type', 'deal', 'created_by', 'created_at')
    list_filter = ('activity_type',)
    search_fields = ('title', 'description')
