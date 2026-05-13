from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    ROLE_CHOICES = (
        ("STUDENT", "Student"),
        ("TUTOR", "Tutor"),
    )

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("INTERVIEW", "Interview"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="STUDENT")

    # السيرة الذاتية
    cv = models.FileField(upload_to="cvs/", null=True, blank=True)

    # حالة قبول المعلّم
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    # ملاحظة من الإدارة
    admin_note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
    def __str__(self):
        return f"{self.user.username} - {self.role}"