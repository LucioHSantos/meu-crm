from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone
from django.utils.html import escape
import json

from apps.contacts.models import Contact
from apps.deals.models import Deal, DealActivity
from apps.tasks.models import Task


STAGE_LABELS = {
    'prospecting': 'Prospecção',
    'qualification': 'Qualificação',
    'proposal': 'Proposta',
    'negotiation': 'Negociação',
    'closed_won': 'Ganho',
    'closed_lost': 'Perdido',
}


@login_required
def index(request):
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_contacts = Contact.objects.count()
    total_leads = Contact.objects.filter(status='lead').count()
    total_prospects = Contact.objects.filter(status='prospect').count()
    total_clients = Contact.objects.filter(status='client').count()

    total_deals = Deal.objects.count()
    deal_values = Deal.objects.aggregate(
        total_value=Sum('value'),
        won_value=Sum('value', filter=Q(stage='closed_won')),
        lost_value=Sum('value', filter=Q(stage='closed_lost')),
    )

    total_value = deal_values['total_value'] or 0
    won_value = deal_values['won_value'] or 0
    lost_value = deal_values['lost_value'] or 0

    won_count = Deal.objects.filter(stage='closed_won').count()
    conversion_rate = (won_count / total_deals * 100) if total_deals > 0 else 0

    deals_by_stage = dict(
        Deal.objects.values_list('stage').annotate(count=Count('id')).values_list('stage', 'count')
    )

    chart_stage_keys = json.dumps(list(deals_by_stage.keys()))
    chart_stage_labels = json.dumps([STAGE_LABELS.get(k, k) for k in deals_by_stage.keys()])
    chart_stage_counts = json.dumps(list(deals_by_stage.values()))

    recent_activities = (
        DealActivity.objects
        .select_related('deal', 'created_by')
        .order_by('-created_at')[:10]
    )

    tasks_pending = Task.objects.filter(status__in=['pending', 'in_progress']).count()
    tasks_overdue = Task.objects.filter(
        status__in=['pending', 'in_progress'],
        due_date__lt=timezone.now(),
    ).count()

    monthly_deals = Deal.objects.filter(created_at__gte=start_of_month).count()

    context = {
        'total_contacts': total_contacts,
        'total_leads': total_leads,
        'total_prospects': total_prospects,
        'total_clients': total_clients,
        'total_deals': total_deals,
        'total_value': total_value,
        'won_value': won_value,
        'lost_value': lost_value,
        'deals_by_stage': deals_by_stage,
        'chart_stage_keys': chart_stage_keys,
        'chart_stage_labels': chart_stage_labels,
        'chart_stage_counts': chart_stage_counts,
        'recent_activities': recent_activities,
        'tasks_pending': tasks_pending,
        'tasks_overdue': tasks_overdue,
        'monthly_deals': monthly_deals,
        'conversion_rate': round(conversion_rate, 2),
    }

    return render(request, 'dashboard/index.html', context)
