from django.db.models import Count, Sum, Q, F
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.contacts.models import Contact
from apps.deals.models import Deal, DealActivity
from apps.tasks.models import Task

from .serializers import ContactSerializer, DealSerializer, TaskSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_metrics(request):
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

    recent_activities = DealActivity.objects.select_related('deal', 'created_by').order_by('-created_at')[:10]

    tasks_pending = Task.objects.filter(status__in=['pending', 'in_progress']).count()
    tasks_overdue = Task.objects.filter(
        status__in=['pending', 'in_progress'],
        due_date__lt=timezone.now(),
    ).count()

    monthly_deals = Deal.objects.filter(created_at__gte=start_of_month).count()

    return Response({
        'total_contacts': total_contacts,
        'total_leads': total_leads,
        'total_prospects': total_prospects,
        'total_clients': total_clients,
        'total_deals': total_deals,
        'total_value': total_value,
        'won_value': won_value,
        'lost_value': lost_value,
        'deals_by_stage': deals_by_stage,
        'recent_activities': [
            {
                'id': a.id,
                'deal_title': a.deal.title,
                'activity_type': a.activity_type,
                'title': a.title,
                'description': a.description,
                'created_by': a.created_by.username,
                'created_at': a.created_at,
            }
            for a in recent_activities
        ],
        'tasks_pending': tasks_pending,
        'tasks_overdue': tasks_overdue,
        'monthly_deals': monthly_deals,
        'conversion_rate': round(conversion_rate, 2),
    })


class DealListAPI(generics.ListCreateAPIView):
    queryset = Deal.objects.select_related('contact', 'assigned_to').all()
    serializer_class = DealSerializer


class DealDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Deal.objects.select_related('contact', 'assigned_to').all()
    serializer_class = DealSerializer


class ContactListAPI(generics.ListCreateAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer


class ContactDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer


class TaskListAPI(generics.ListCreateAPIView):
    queryset = Task.objects.select_related('assigned_to', 'contact').all()
    serializer_class = TaskSerializer


class TaskDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.select_related('assigned_to', 'contact').all()
    serializer_class = TaskSerializer
