from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Contact, ContactNote
from .forms import ContactForm, ContactNoteForm, ContactFilterForm

User = get_user_model()


@login_required
def contact_list(request):
    contacts = Contact.objects.select_related('assigned_to').all()

    search = request.GET.get('search', '').strip()
    if search:
        contacts = contacts.filter(name__icontains=search)

    form = ContactFilterForm(request.GET or None, user_queryset=User.objects.all())
    if form.is_valid():
        status = form.cleaned_data.get('status')
        source = form.cleaned_data.get('source')
        assigned_to = form.cleaned_data.get('assigned_to')
        if status:
            contacts = contacts.filter(status=status)
        if source:
            contacts = contacts.filter(source=source)
        if assigned_to:
            contacts = contacts.filter(assigned_to=assigned_to)

    context = {
        'contacts': contacts,
        'filter_form': form,
        'search': search,
    }
    return render(request, 'contacts/contact_list.html', context)


@login_required
def contact_detail(request, pk):
    contact = get_object_or_404(
        Contact.objects.select_related('assigned_to'),
        pk=pk,
    )
    contact_notes = contact.contact_notes.select_related('author').all()
    note_form = ContactNoteForm()

    related_deals = contact.deals.all()[:5]
    from apps.tasks.models import Task
    related_tasks = Task.objects.filter(contact=contact)[:5] if hasattr(Task, 'contact') else []

    total_deals = contact.deals.count()
    total_value = sum(d.value for d in contact.deals.all())
    pending_tasks_count = 0
    for task in related_tasks:
        if hasattr(task, 'status') and task.status != 'completed':
            pending_tasks_count += 1

    context = {
        'contact': contact,
        'contact_notes': contact_notes,
        'note_form': note_form,
        'related_deals': related_deals,
        'related_tasks': related_tasks,
        'total_deals': total_deals,
        'total_value': total_value,
        'pending_tasks': pending_tasks_count,
        'today': timezone.now().date(),
    }
    return render(request, 'contacts/contact_detail.html', context)


@login_required
def contact_create(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            messages.success(request, f'Contact "{contact.name}" created successfully.')
            return redirect('contacts:detail', pk=contact.pk)
    else:
        form = ContactForm()

    context = {
        'form': form,
        'title': 'Create Contact',
        'users': User.objects.all(),
    }
    return render(request, 'contacts/contact_form.html', context)


@login_required
def contact_edit(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            contact = form.save()
            messages.success(request, f'Contact "{contact.name}" updated successfully.')
            return redirect('contacts:detail', pk=contact.pk)
    else:
        form = ContactForm(instance=contact)

    context = {
        'form': form,
        'contact': contact,
        'title': 'Edit Contact',
        'users': User.objects.all(),
    }
    return render(request, 'contacts/contact_form.html', context)


@login_required
def contact_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == 'POST':
        name = contact.name
        contact.delete()
        messages.success(request, f'Contact "{name}" deleted successfully.')
        return redirect('contacts:list')

    context = {
        'contact': contact,
    }
    return render(request, 'contacts/contact_confirm_delete.html', context)


@login_required
@require_POST
def contact_note_add(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    form = ContactNoteForm(request.POST)
    if form.is_valid():
        note = form.save(commit=False)
        note.contact = contact
        note.author = request.user
        note.save()
        messages.success(request, 'Note added successfully.')
    else:
        messages.error(request, 'Failed to add note. Please check the form.')

    return redirect('contacts:detail', pk=contact.pk)
