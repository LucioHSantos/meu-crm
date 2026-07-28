import calendar

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import TaskFilterForm, TaskForm
from .models import Task

User = get_user_model()


@login_required
def task_list(request):
    tasks = Task.objects.filter(assigned_to=request.user)

    filter_form = TaskFilterForm(request.GET, user_queryset=User.objects.all())

    status = request.GET.get('status')
    priority = request.GET.get('priority')

    if status:
        tasks = tasks.filter(status=status)
    if priority:
        tasks = tasks.filter(priority=priority)

    now = timezone.now()
    overdue_tasks = []
    for task in tasks:
        if task.is_overdue:
            overdue_tasks.append(task.pk)

    context = {
        'tasks': tasks,
        'filter_form': filter_form,
        'overdue_task_ids': overdue_tasks,
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    return render(request, 'tasks/task_detail.html', {'task': task})


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Task "{task.title}" created successfully.')
            return redirect('tasks:detail', pk=task.pk)
    else:
        form = TaskForm()
    return render(request, 'tasks/task_form.html', {'form': form, 'action': 'Create'})


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Task "{task.title}" updated successfully.')
            return redirect('tasks:detail', pk=task.pk)
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks/task_form.html', {'form': form, 'action': 'Edit'})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'Task "{title}" deleted successfully.')
        return redirect('tasks:list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
def task_toggle_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    status_order = ['pending', 'in_progress', 'completed']
    current_index = status_order.index(task.status)
    next_index = (current_index + 1) % len(status_order)
    task.status = status_order[next_index]
    task.save()
    messages.success(request, f'Task "{task.title}" status changed to {task.get_status_display()}.')
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('tasks:list')


@login_required
def task_calendar(request):
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))

    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    month_name = calendar.month_name[month]
    cal = calendar.monthcalendar(year, month)

    start_of_month = timezone.datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
    if month == 12:
        end_of_month = timezone.datetime(year + 1, 1, 1, tzinfo=timezone.get_current_timezone())
    else:
        end_of_month = timezone.datetime(year, month + 1, 1, tzinfo=timezone.get_current_timezone())

    tasks = Task.objects.filter(
        assigned_to=request.user,
        due_date__gte=start_of_month,
        due_date__lt=end_of_month,
    )

    tasks_by_day = {}
    for task in tasks:
        day = task.due_date.day
        tasks_by_day.setdefault(day, []).append(task)

    calendar_data = []
    for week in cal:
        week_data = []
        for day in week:
            week_data.append({
                'day': day,
                'tasks': tasks_by_day.get(day, []),
            })
        calendar_data.append(week_data)

    context = {
        'year': year,
        'month': month,
        'month_name': month_name,
        'calendar_data': calendar_data,
        'today': timezone.now(),
    }
    return render(request, 'tasks/task_calendar.html', context)
