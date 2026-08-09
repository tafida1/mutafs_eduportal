from django.conf import settings
from django.db import models


class Conversation(models.Model):

    class ConversationType(models.TextChoices):
        DIRECT = "DIRECT", "Direct"
        ANNOUNCEMENT = "ANNOUNCEMENT", "Announcement"

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="conversations",
    )

    title = models.CharField(max_length=255, blank=True)

    conversation_type = models.CharField(
        max_length=20,
        choices=ConversationType.choices,
        default=ConversationType.DIRECT,
    )

    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="message_conversations",
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_conversations",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or f"Conversation #{self.id}"


class Message(models.Model):

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )

    body = models.TextField()

    attachment = models.FileField(
        upload_to="messages/",
        blank=True,
        null=True,
    )

    is_system_message = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender} - {self.created_at}"


class MessageReadStatus(models.Model):

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="read_statuses",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    is_read = models.BooleanField(default=False)

    read_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    class Meta:
        unique_together = ("message", "user")