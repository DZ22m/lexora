from django.db import models
from django.contrib.auth.models import User

class Tutor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    photo = models.ImageField(upload_to="tutors/photos/", blank=True, null=True)

    name = models.CharField(max_length=120)
    language = models.CharField(max_length=50)
    country = models.CharField(max_length=60)
    price = models.PositiveIntegerField(help_text="Price per hour in AED")
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=4.8)
    bio = models.TextField(blank=True)
    lessons = models.PositiveIntegerField(default=0)
    students = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.language})"

from django.contrib.auth.models import User

class Booking(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="student_bookings")
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name="tutor_bookings")

    lesson_date = models.DateField()
    lesson_time = models.TimeField()
    note = models.TextField(blank=True)

    is_paid = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tutor_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="USD")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} booked {self.tutor.name} on {self.lesson_date}"
