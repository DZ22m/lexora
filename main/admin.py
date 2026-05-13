from django.contrib import admin
from .models import Tutor, Booking

admin.site.register(Tutor)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "tutor", "lesson_date", "lesson_time", "amount", "platform_fee", "tutor_earnings", "currency", "is_paid")