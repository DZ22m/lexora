from django.contrib import admin

from .models import Profile
from .views import send_lexora_email


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "status")
    list_filter = ("status", "role")
    search_fields = ("user__username", "user__email")

    def save_model(self, request, obj, form, change):
        old_status = None

        if obj.pk:
            try:
                old_status = Profile.objects.get(pk=obj.pk).status
            except Profile.DoesNotExist:
                pass

        super().save_model(request, obj, form, change)

        if old_status == obj.status:
            return

        if not obj.user.email:
            return

        if obj.status == "APPROVED":
            send_lexora_email(
                obj.user.email,
                "تم قبول طلبك في Lexora 🎉",
                f"""
                <div style="font-family: Arial; direction: rtl; text-align: right;">
                    <h2>مبروك 🎉</h2>
                    <p>تمت الموافقة على طلبك كمعلم في Lexora.</p>
                    <p>يمكنك الآن البدء باستقبال الطلاب والحجوزات.</p>
                    <p>{obj.admin_note or ''}</p>
                </div>
                """
            )

        elif obj.status == "INTERVIEW":
            send_lexora_email(
                obj.user.email,
                "تحديث بخصوص طلبك في Lexora",
                f"""
                <div style="font-family: Arial; direction: rtl; text-align: right;">
                    <h2>مرحبًا {obj.user.username}</h2>
                    <p>تم تحويل طلبك إلى مرحلة المقابلة.</p>
                    <p>{obj.admin_note or ''}</p>
                </div>
                """
            )

        elif obj.status == "REJECTED":
            send_lexora_email(
                obj.user.email,
                "تحديث بخصوص طلب المعلم في Lexora",
                f"""
                <div style="font-family: Arial; direction: rtl; text-align: right;">
                    <h2>مرحبًا {obj.user.username}</h2>
                    <p>نعتذر، لم تتم الموافقة على الطلب في الوقت الحالي.</p>
                    <p>{obj.admin_note or ''}</p>
                </div>
                """
            )

