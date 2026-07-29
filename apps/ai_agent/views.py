import httpx
import json
import logging
import os
import re
import tempfile

from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import (
    AIAgentForm,
    KnowledgeBaseForm,
    TrainingDataForm,
    ConversationFilterForm,
    KnowledgeBulkForm,
    KnowledgeDocumentForm,
    KnowledgeURLForm,
)
from .models import AIAgent, KnowledgeBase, KnowledgeDocument, TrainingData, Conversation, Message

User = get_user_model()

logger = logging.getLogger(__name__)


def _get_or_create_agent():
    agent, _ = AIAgent.objects.get_or_create(
        pk=1,
        defaults={'name': 'AI Assistant'},
    )
    return agent


@login_required
def agent_config(request):
    agent = _get_or_create_agent()

    if request.method == 'POST':
        form = AIAgentForm(request.POST, instance=agent)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configurações salvas com sucesso.')
            return redirect('ai_agent:config')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = AIAgentForm(instance=agent)

    context = {
        'form': form,
        'agent': agent,
        'knowledge_count': KnowledgeBase.objects.filter(agent=agent).count(),
        'training_count': TrainingData.objects.filter(agent=agent).count(),
        'active_conversations': Conversation.objects.filter(agent=agent, status='bot_active').count(),
    }
    return render(request, 'ai_agent/config.html', context)


@login_required
def knowledge_list(request):
    agent = _get_or_create_agent()
    items = KnowledgeBase.objects.filter(agent=agent).order_by('category', 'question')
    items_by_category = {}
    for item in items:
        items_by_category.setdefault(item.category, []).append(item)

    categories_with_counts = []
    for cat_key, cat_label in KnowledgeBase.CATEGORY_CHOICES:
        cat_items = items_by_category.get(cat_key, [])
        if cat_items:
            categories_with_counts.append({
                'key': cat_key,
                'label': cat_label,
                'items': cat_items,
                'count': len(cat_items),
            })

    documents = KnowledgeDocument.objects.filter(agent=agent).order_by('-created_at')

    context = {
        'agent': agent,
        'categories': categories_with_counts,
        'total_count': items.count(),
        'documents': documents,
        'doc_form': KnowledgeDocumentForm(),
        'url_form': KnowledgeURLForm(),
    }
    return render(request, 'ai_agent/knowledge_list.html', context)


@login_required
def knowledge_create(request):
    agent = _get_or_create_agent()

    if request.method == 'POST':
        form = KnowledgeBaseForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.agent = agent
            item.save()
            messages.success(request, 'Knowledge item created successfully.')
            return redirect('ai_agent:knowledge_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = KnowledgeBaseForm()

    context = {
        'form': form,
        'title': 'Add Knowledge Item',
    }
    return render(request, 'ai_agent/knowledge_form.html', context)


@login_required
def knowledge_edit(request, pk):
    agent = _get_or_create_agent()
    item = get_object_or_404(KnowledgeBase, pk=pk, agent=agent)

    if request.method == 'POST':
        form = KnowledgeBaseForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Knowledge item updated successfully.')
            return redirect('ai_agent:knowledge_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = KnowledgeBaseForm(instance=item)

    context = {
        'form': form,
        'item': item,
        'title': 'Edit Knowledge Item',
    }
    return render(request, 'ai_agent/knowledge_form.html', context)


@login_required
def knowledge_delete(request, pk):
    agent = _get_or_create_agent()
    item = get_object_or_404(KnowledgeBase, pk=pk, agent=agent)

    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Knowledge item deleted successfully.')
        return redirect('ai_agent:knowledge_list')

    context = {
        'item': item,
    }
    return render(request, 'ai_agent/knowledge_confirm_delete.html', context)


@login_required
@require_POST
def knowledge_bulk(request):
    agent = _get_or_create_agent()
    form = KnowledgeBulkForm(request.POST)

    if form.is_valid():
        items_text = form.cleaned_data['items']
        category = form.cleaned_data['category']
        lines = [line.strip() for line in items_text.strip().split('\n') if line.strip()]
        created_count = 0

        for line in lines:
            if '|' in line:
                question, answer = line.split('|', 1)
                question = question.strip()
                answer = answer.strip()
                if question and answer:
                    KnowledgeBase.objects.create(
                        agent=agent,
                        category=category,
                        question=question,
                        answer=answer,
                    )
                    created_count += 1

        messages.success(request, f'{created_count} knowledge item(s) created successfully.')
    else:
        messages.error(request, 'Please correct the errors below.')

    return redirect('ai_agent:knowledge_list')


def _extract_text_from_file(file_obj):
    ext = os.path.splitext(file_obj.name)[1].lower()
    try:
        if ext == '.txt':
            return file_obj.read().decode('utf-8', errors='replace')
        elif ext == '.pdf':
            from pypdf import PdfReader
            reader = PdfReader(file_obj)
            return '\n'.join(page.extract_text() for page in reader.pages if page.extract_text())
        elif ext == '.docx':
            import docx
            doc = docx.Document(file_obj)
            return '\n'.join(p.text for p in doc.paragraphs)
    except Exception as e:
        logger.exception(f'Error extracting text from {file_obj.name}: {e}')
    return ''


def _scrape_url_text(url):
    try:
        resp = httpx.get(url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        text = soup.get_text(separator='\n')
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        return '\n'.join(lines[:200])
    except Exception as e:
        logger.exception(f'Error scraping URL {url}: {e}')
    return ''


def _split_text_into_items(text, max_chars=500):
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    items = []
    current = ''
    for p in paragraphs:
        if len(current) + len(p) < max_chars:
            current += '\n' + p if current else p
        else:
            if current:
                items.append(current)
            current = p
    if current:
        items.append(current)
    return items


@login_required
def knowledge_document_upload(request):
    agent = _get_or_create_agent()
    if request.method == 'POST':
        form = KnowledgeDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.agent = agent
            doc.save()
            doc.refresh_from_db()
            text = _extract_text_from_file(doc.file)
            if text:
                doc.extracted_text = text[:50000]
                doc.save()
                items = _split_text_into_items(text)
                created = 0
                for item in items[:50]:
                    q = item[:80]
                    a = item
                    if not KnowledgeBase.objects.filter(agent=agent, question=q).exists():
                        KnowledgeBase.objects.create(agent=agent, category=doc.category, question=q, answer=a)
                        created += 1
                messages.success(request, f'Document processed. {created} knowledge items auto-created.')
            else:
                messages.warning(request, 'Document uploaded but no text could be extracted.')
            return redirect('ai_agent:knowledge_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = KnowledgeDocumentForm()
    return render(request, 'ai_agent/knowledge_form.html', {'form': form, 'title': 'Upload Document'})


@login_required
def knowledge_learn_url(request):
    agent = _get_or_create_agent()
    if request.method == 'POST':
        form = KnowledgeURLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            category = form.cleaned_data['category']
            text = _scrape_url_text(url)
            if text:
                items = _split_text_into_items(text)
                created = 0
                for item in items[:50]:
                    q = item[:80]
                    a = item
                    if not KnowledgeBase.objects.filter(agent=agent, question=q).exists():
                        KnowledgeBase.objects.create(agent=agent, category=category, question=q, answer=a)
                        created += 1
                KnowledgeDocument.objects.create(
                    agent=agent, title=f'URL: {url}', category=category,
                    extracted_text=text[:50000], source_url=url,
                )
                messages.success(request, f'URL processed. {created} knowledge items auto-created.')
            else:
                messages.error(request, 'Could not extract content from URL.')
            return redirect('ai_agent:knowledge_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = KnowledgeURLForm()
    return render(request, 'ai_agent/knowledge_form.html', {'form': form, 'title': 'Learn from URL'})


@login_required
@require_POST
def knowledge_document_delete(request, pk):
    agent = _get_or_create_agent()
    doc = get_object_or_404(KnowledgeDocument, pk=pk, agent=agent)
    if doc.file:
        doc.file.delete(save=False)
    doc.delete()
    messages.success(request, 'Document deleted.')
    return redirect('ai_agent:knowledge_list')


@login_required
def training_list(request):
    agent = _get_or_create_agent()
    training_data = TrainingData.objects.filter(agent=agent)
    knowledge_items = KnowledgeBase.objects.filter(agent=agent, is_active=True)

    context = {
        'agent': agent,
        'training_data': training_data,
        'knowledge_items': knowledge_items,
    }
    return render(request, 'ai_agent/training_list.html', context)


@login_required
def training_test_page(request):
    agent = _get_or_create_agent()
    knowledge_items = KnowledgeBase.objects.filter(agent=agent, is_active=True)

    context = {
        'agent': agent,
        'knowledge_items': knowledge_items,
    }
    return render(request, 'ai_agent/training_test.html', context)


@login_required
def training_test_send(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json as json_mod
    try:
        data = json_mod.loads(request.body)
        user_message = data.get('message', '').strip()
    except (json_mod.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not user_message:
        return JsonResponse({'error': 'Empty message'}, status=400)

    agent = _get_or_create_agent()

    try:
        response_text = _get_ai_response(agent, user_message)
    except Exception as e:
        logger.exception('AI test error')
        response_text = f'Erro ao conectar com o modelo de IA. Verifique se o Ollama está rodando. Erro: {str(e)}'

    return JsonResponse({'response': response_text})


@login_required
def training_create(request):
    agent = _get_or_create_agent()

    if request.method == 'POST':
        form = TrainingDataForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.agent = agent
            entry.save()
            messages.success(request, 'Dado de treinamento criado com sucesso.')
            return redirect('ai_agent:training_list')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = TrainingDataForm()

    context = {
        'form': form,
    }
    return render(request, 'ai_agent/training_form.html', context)


@login_required
@require_POST
def training_delete(request, pk):
    agent = _get_or_create_agent()
    entry = get_object_or_404(TrainingData, pk=pk, agent=agent)
    entry.delete()
    messages.success(request, 'Dado de treinamento excluído com sucesso.')
    return redirect('ai_agent:training_list')


@login_required
def conversation_list(request):
    agent = _get_or_create_agent()
    conversations = Conversation.objects.filter(agent=agent).select_related('contact', 'assigned_to')

    form = ConversationFilterForm(request.GET or None)
    if form.is_valid():
        status = form.cleaned_data.get('status')
        assigned_to = form.cleaned_data.get('assigned_to')
        if status:
            conversations = conversations.filter(status=status)
        if assigned_to:
            conversations = conversations.filter(assigned_to=assigned_to)

    context = {
        'conversations': conversations,
        'filter_form': form,
    }
    return render(request, 'ai_agent/conversation_list.html', context)


@login_required
def conversation_detail(request, pk):
    agent = _get_or_create_agent()
    conversation = get_object_or_404(
        Conversation.objects.select_related('contact', 'assigned_to'),
        pk=pk,
        agent=agent,
    )
    messages_list = conversation.messages.all()

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                conversation=conversation,
                sender_type='human_agent',
                content=content,
            )
            conversation.unread_count = 0
            conversation.save()
            last_user_msg = messages_list.filter(sender_type='user').last()
            if last_user_msg and len(content) > 10:
                exists = TrainingData.objects.filter(
                    agent=agent,
                    input_message=last_user_msg.content[:200],
                    expected_response=content[:200],
                ).exists()
                if not exists:
                    TrainingData.objects.create(
                        agent=agent,
                        input_message=last_user_msg.content[:500],
                        expected_response=content[:500],
                    )
            messages.success(request, 'Message sent successfully.')
        else:
            messages.error(request, 'Message cannot be empty.')

        return redirect('ai_agent:conversation_detail', pk=pk)

    contact = conversation.contact
    context = {
        'conversation': conversation,
        'messages_list': messages_list,
        'contact': contact,
    }
    return render(request, 'ai_agent/conversation_detail.html', context)


@login_required
@require_POST
def conversation_handoff(request, pk):
    agent = _get_or_create_agent()
    conversation = get_object_or_404(Conversation, pk=pk, agent=agent)

    conversation.status = 'waiting_human'
    conversation.assigned_to = request.user
    conversation.save()

    messages.success(request, 'You have taken over this conversation.')
    return redirect('ai_agent:conversation_detail', pk=pk)


@login_required
@require_POST
def conversation_close(request, pk):
    agent = _get_or_create_agent()
    conversation = get_object_or_404(Conversation, pk=pk, agent=agent)

    conversation.status = 'closed'
    conversation.assigned_to = request.user
    conversation.save()

    messages.success(request, 'Conversation closed.')
    return redirect('ai_agent:conversation_list')


@csrf_exempt
def webhook(request):
    if request.method == 'GET':
        hub_mode = request.GET.get('hub.mode')
        hub_verify_token = request.GET.get('hub.verify_token')
        hub_challenge = request.GET.get('hub.challenge')

        if hub_mode == 'subscribe' and hub_verify_token == getattr(
            django_settings, 'WHATSAPP_VERIFY_TOKEN', ''
        ):
            return HttpResponse(hub_challenge)
        return HttpResponseBadRequest('Verification failed')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON')

        try:
            entry = data.get('entries', [{}])[0]
            change = entry.get('changes', [{}])[0]
            value = change.get('value', {})

            messages_data = value.get('messages', [])
            contacts_data = value.get('contacts', [])

            if messages_data:
                msg = messages_data[0]
                phone_number = msg.get('from', '')
                message_body = msg.get('text', {}).get('body', '')
                whatsapp_message_id = msg.get('id', '')
                msg_type = msg.get('type', '')

                sender_name = ''
                if contacts_data:
                    sender_name = contacts_data[0].get('profile', {}).get('name', '')

                if msg_type == 'text' and message_body:
                    _process_incoming_message(
                        phone_number=phone_number,
                        message_body=message_body,
                        sender_name=sender_name,
                        whatsapp_message_id=whatsapp_message_id,
                    )

        except Exception as e:
            logger.exception('Webhook processing error: %s', e)

        return HttpResponse('OK')

    return HttpResponseBadRequest('Method not allowed')


@csrf_exempt
def bridge_incoming(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    phone_number = data.get('phone_number', '')
    message_body = data.get('message_body', '')
    sender_name = data.get('sender_name', '')
    whatsapp_message_id = data.get('whatsapp_message_id', '')

    if phone_number and message_body:
        _process_incoming_message(
            phone_number=phone_number,
            message_body=message_body,
            sender_name=sender_name,
            whatsapp_message_id=whatsapp_message_id,
        )

    return HttpResponse('OK')


def _bridge_url():
    return getattr(django_settings, 'WHATSAPP_BRIDGE_URL', 'http://127.0.0.1:3001')


@login_required
def whatsapp_page(request):
    return render(request, 'ai_agent/whatsapp.html')


@login_required
def whatsapp_status_api(request):
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f'{_bridge_url()}/status')
            bridge_status = r.json()
    except Exception:
        bridge_status = {'status': 'unreachable', 'hasQr': False}

    can_connect = bridge_status.get('status') == 'connected'

    return JsonResponse({
        'status': bridge_status.get('status', 'unreachable'),
        'hasQr': bridge_status.get('hasQr', False),
        'can_send': can_connect,
    })


@login_required
def whatsapp_qr_api(request):
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f'{_bridge_url()}/qr')
            data = r.json()
            return JsonResponse(data)
    except Exception:
        return JsonResponse({'error': 'Bridge unreachable'}, status=503)


def _process_incoming_message(phone_number, message_body, sender_name, whatsapp_message_id):
    from apps.contacts.models import Contact

    contact, _ = Contact.objects.get_or_create(
        phone=phone_number,
        defaults={
            'name': sender_name or phone_number,
            'source': 'other',
        },
    )

    agent = _get_or_create_agent()

    conversation = Conversation.objects.filter(
        contact=contact,
        agent=agent,
        status__in=['bot_active', 'waiting_human'],
    ).first()

    if conversation is None:
        conversation = Conversation.objects.create(
            contact=contact,
            agent=agent,
            status='bot_active',
        )

    if conversation.status == 'waiting_human':
        Message.objects.create(
            conversation=conversation,
            sender_type='user',
            content=message_body,
            whatsapp_message_id=whatsapp_message_id,
        )
        return

    Message.objects.create(
        conversation=conversation,
        sender_type='user',
        content=message_body,
        whatsapp_message_id=whatsapp_message_id,
    )

    try:
        ai_response = _get_ai_response(agent, message_body, conversation=conversation)
    except Exception as e:
        logger.exception('AI response error')
        ai_response = 'Desculpe, estou com dificuldades técnicas no momento. Por favor, tente novamente mais tarde.'

    Message.objects.create(
        conversation=conversation,
        sender_type='bot',
        content=ai_response,
    )

    conversation.unread_count += 1
    conversation.save()

    send_whatsapp_message(phone_number, ai_response)


def _get_ai_response(agent, user_message, conversation=None):
    context_messages = []
    if conversation:
        recent = conversation.messages.order_by('-created_at')[:20]
        for m in reversed(recent):
            role = 'assistant' if m.sender_type in ('bot', 'human_agent') else 'user'
            context_messages.append({'role': role, 'content': m.content})

    knowledge_items = KnowledgeBase.objects.filter(
        agent=agent,
        is_active=True,
    ).order_by('category', 'question')

    knowledge_text = ''
    for item in knowledge_items:
        knowledge_text += f"\n[{item.get_category_display()}] Q: {item.question}\nA: {item.answer}\n"

    training_items = TrainingData.objects.filter(agent=agent, available=True).order_by('?')[:5]

    business_info = ''
    if agent.business_name:
        business_info += f"\nBusiness: {agent.business_name}"
    if agent.business_description:
        business_info += f"\nDescription: {agent.business_description}"

    system_prompt = agent.system_prompt or 'You are a helpful sales and support assistant.'

    if knowledge_text:
        system_prompt += f"\n\nKnowledge Base:{knowledge_text}"

    if training_items:
        system_prompt += "\n\nExample conversations to learn from:"
        for t in training_items:
            system_prompt += f"\n\nCustomer: {t.input_message}\nAssistant: {t.expected_response}"

    if business_info:
        system_prompt += f"\n\nBusiness Information:{business_info}"

    messages_list = [{'role': 'system', 'content': system_prompt}]
    messages_list.extend(context_messages)
    messages_list.append({'role': 'user', 'content': user_message})

    ollama_url = getattr(django_settings, 'OLLAMA_URL', 'http://localhost:11434')
    model = agent.ollama_model or 'llama3'

    payload = {
        'model': model,
        'messages': messages_list,
        'stream': False,
        'options': {
            'temperature': agent.temperature,
            'num_predict': agent.max_tokens,
        },
    }

    with httpx.Client(timeout=60.0) as client:
        response = client.post(f'{ollama_url}/api/chat', json=payload)
        response.raise_for_status()
        result = response.json()

    return result.get('message', {}).get('content', 'I could not generate a response.')


def send_whatsapp_message(phone_number, message):
    bridge_url = _bridge_url()

    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(f'{bridge_url}/send', json={
                'to': phone_number,
                'message': message,
            })
            if r.status_code == 200:
                logger.info('WhatsApp message sent via bridge to %s', phone_number)
                return
    except Exception:
        logger.info('Bridge unavailable, falling back to Meta API')

    phone_number_id = getattr(django_settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
    access_token = getattr(django_settings, 'WHATSAPP_ACCESS_TOKEN', '')
    api_version = getattr(django_settings, 'WHATSAPP_API_VERSION', 'v18.0')

    if not phone_number_id or not access_token:
        logger.warning('WhatsApp credentials not configured - message not sent')
        return

    url = f'https://graph.facebook.com/{api_version}/{phone_number_id}/messages'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'messaging_product': 'whatsapp',
        'to': phone_number,
        'type': 'text',
        'text': {
            'body': message,
        },
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info('WhatsApp message sent via Meta API to %s', phone_number)
    except Exception as e:
        logger.exception('Failed to send WhatsApp message: %s', e)
