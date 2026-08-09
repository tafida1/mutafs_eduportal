from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import User
from apps.core.decorators import role_required
from django.contrib import messages
from .forms import MessageForm, StartConversationForm
from .models import Conversation, Message, MessageReadStatus


@login_required
def conversation_list(request):
    conversations = Conversation.objects.filter(
        participants=request.user,
    ).prefetch_related(
        "participants",
        "messages",
    )

    conversation_data = []

    for conversation in conversations:
        unread_count = MessageReadStatus.objects.filter(
            message__conversation=conversation,
            user=request.user,
            is_read=False,
        ).count()

        last_message = conversation.messages.order_by("-created_at").first()

        conversation_data.append({
            "conversation": conversation,
            "unread_count": unread_count,
            "last_message": last_message,
        })

    return render(request, "messaging/conversation_list.html", {
        "conversation_data": conversation_data,
    })


    

@login_required
def conversation_detail(request, conversation_id):

    conversation = get_object_or_404(
        Conversation.objects.prefetch_related(
            "participants",
            "messages__sender",
        ),
        pk=conversation_id,
        participants=request.user,
    )

    messages = conversation.messages.select_related("sender")

    for message in messages.exclude(sender=request.user):

        status, _ = MessageReadStatus.objects.get_or_create(
            message=message,
            user=request.user,
        )

        if not status.is_read:
            status.is_read = True
            status.read_at = timezone.now()
            status.save()

    if request.method == "POST":

        form = MessageForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            message = form.save(commit=False)

            message.conversation = conversation
            message.sender = request.user

            message.save()

            for participant in conversation.participants.exclude(
                id=request.user.id
            ):

                MessageReadStatus.objects.get_or_create(
                    message=message,
                    user=participant,
                )

            return redirect(
                "conversation_detail",
                conversation_id=conversation.id,
            )

    else:
        form = MessageForm()

    return render(request, "messaging/conversation_detail.html", {
        "conversation": conversation,
        "messages": messages,
        "form": form,
    })


@login_required
def create_direct_conversation(request, user_id):

    target_user = get_object_or_404(User, pk=user_id)

    conversation = Conversation.objects.create(
        school=request.user.school,
        created_by=request.user,
        conversation_type=Conversation.ConversationType.DIRECT,
    )

    conversation.participants.add(
        request.user,
        target_user,
    )

    return redirect(
        "conversation_detail",
        conversation_id=conversation.id,
    )



@login_required
def start_conversation(request):
    if request.method == "POST":
        form = StartConversationForm(
            request.POST,
            request.FILES,
            user=request.user,
        )

        if form.is_valid():
            recipient = form.cleaned_data["recipient"]
            message_body = form.cleaned_data["message"]
            attachment = form.cleaned_data.get("attachment")

            if not request.user.is_super_admin and recipient.school != request.user.school:
                messages.error(request, "You cannot message users outside your school.")
                return redirect("conversation_list")

            conversation = Conversation.objects.create(
                school=request.user.school or recipient.school,
                created_by=request.user,
                conversation_type=Conversation.ConversationType.DIRECT,
                title=f"{request.user.get_full_name()} ↔ {recipient.get_full_name()}",
            )

            conversation.participants.add(request.user, recipient)

            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                body=message_body,
                attachment=attachment,
            )

            MessageReadStatus.objects.get_or_create(
                message=message,
                user=recipient,
            )

            messages.success(request, "Conversation started successfully.")
            return redirect("conversation_detail", conversation_id=conversation.id)

    else:
        form = StartConversationForm(user=request.user)

    return render(request, "messaging/start_conversation.html", {
        "form": form,
    })