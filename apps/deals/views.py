import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .models import Deal, DealActivity
from .forms import DealForm, DealActivityForm, DealFilterForm

User = get_user_model()


@login_required
def deal_list(request):
    deals = Deal.objects.select_related('contact', 'assigned_to').all()

    form = DealFilterForm(request.GET or None, users=User.objects.all())
    if form.is_valid():
        stage = form.cleaned_data.get('stage')
        assigned_to = form.cleaned_data.get('assigned_to')
        priority = form.cleaned_data.get('priority')
        if stage:
            deals = deals.filter(stage=stage)
        if assigned_to:
            deals = deals.filter(assigned_to_id=assigned_to)
        if priority:
            deals = deals.filter(priority=priority)

    context = {
        'deals': deals,
        'filter_form': form,
    }
    return render(request, 'deals/deal_list.html', context)


@login_required
def deal_kanban(request):
    deals = Deal.objects.select_related('contact', 'assigned_to').all()

    form = DealFilterForm(request.GET or None, users=User.objects.all())
    if form.is_valid():
        assigned_to = form.cleaned_data.get('assigned_to')
        priority = form.cleaned_data.get('priority')
        if assigned_to:
            deals = deals.filter(assigned_to_id=assigned_to)
        if priority:
            deals = deals.filter(priority=priority)

    stages = dict(Deal.STAGE_CHOICES)
    kanban_stages = {}
    for stage_key, stage_label in Deal.STAGE_CHOICES:
        stage_deals = deals.filter(stage=stage_key)
        kanban_stages[stage_key] = {
            'label': stage_label,
            'deals': stage_deals,
            'total_value': sum(d.value for d in stage_deals),
        }

    context = {
        'kanban_stages': kanban_stages,
        'stages': Deal.STAGE_CHOICES,
        'filter_form': form,
    }
    return render(request, 'deals/deal_kanban.html', context)


@login_required
def deal_detail(request, pk):
    deal = get_object_or_404(
        Deal.objects.select_related('contact', 'assigned_to'),
        pk=pk,
    )
    activities = deal.activities.select_related('created_by').all()
    activity_form = DealActivityForm()

    context = {
        'deal': deal,
        'activities': activities,
        'activity_form': activity_form,
    }
    return render(request, 'deals/deal_detail.html', context)


@login_required
def deal_create(request):
    if request.method == 'POST':
        form = DealForm(request.POST)
        if form.is_valid():
            deal = form.save()
            messages.success(request, f'Deal "{deal.title}" created successfully.')
            return redirect('deals:detail', pk=deal.pk)
    else:
        form = DealForm()

    context = {
        'form': form,
        'title': 'Create Deal',
    }
    return render(request, 'deals/deal_form.html', context)


@login_required
def deal_edit(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    if request.method == 'POST':
        form = DealForm(request.POST, instance=deal)
        if form.is_valid():
            deal = form.save()
            messages.success(request, f'Deal "{deal.title}" updated successfully.')
            return redirect('deals:detail', pk=deal.pk)
    else:
        form = DealForm(instance=deal)

    context = {
        'form': form,
        'deal': deal,
        'title': 'Edit Deal',
    }
    return render(request, 'deals/deal_form.html', context)


@login_required
def deal_delete(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    if request.method == 'POST':
        title = deal.title
        deal.delete()
        messages.success(request, f'Deal "{title}" deleted successfully.')
        return redirect('deals:list')

    context = {
        'deal': deal,
    }
    return render(request, 'deals/deal_confirm_delete.html', context)


@login_required
@require_POST
def deal_stage_update(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    try:
        data = json.loads(request.body)
        new_stage = data.get('stage')
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid request data'}, status=400)

    valid_stages = [choice[0] for choice in Deal.STAGE_CHOICES]
    if new_stage not in valid_stages:
        return JsonResponse({'error': 'Invalid stage'}, status=400)

    deal.stage = new_stage
    deal.save()

    return JsonResponse({
        'success': True,
        'deal_id': deal.pk,
        'new_stage': new_stage,
        'stage_display': deal.stage_display(),
    })


@login_required
@require_POST
def deal_activity_add(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    form = DealActivityForm(request.POST)
    if form.is_valid():
        activity = form.save(commit=False)
        activity.deal = deal
        activity.created_by = request.user
        activity.save()
        messages.success(request, 'Activity added successfully.')
    else:
        messages.error(request, 'Failed to add activity. Please check the form.')

    return redirect('deals:detail', pk=deal.pk)
