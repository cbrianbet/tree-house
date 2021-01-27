from django.db import models

from authapp.models import Users


class ChatConvo(models.Model):
    message = models.CharField(max_length=600, blank=True)
    message_from = models.ForeignKey(Users, on_delete=models.CASCADE)
    message_to = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="message_to")
    message_read = models.BooleanField(default=False)

    class Meta:
        db_table = "Chat Convos"
