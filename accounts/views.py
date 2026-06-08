```python
import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from .models import Profile
from main.models import Tutor


def send_lexora_email(to_email, subject, html):
    if not settings.RESEND_API_KEY:
        return

    try:
        requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html,
            },
            timeout=20,
        )

    except Exception:
        pass


def register(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        role = request.POST.get("role", "STUDENT")

        if not username or not email or not password:
            messages.error(request, "الرجاء إدخال جميع البيانات المطلوبة.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "اسم المستخدم مستخدم بالفعل، اختاري اسمًا آخر.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "البريد الإلكتروني مستخدم بالفعل.")
            return redirect("register")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        profile = Profile.objects.filter(user=user).first()
        if profile is None:
            profile = Profile.objects.create(
                user=user,
                role=role,
                status="PENDING"
            )
        else:
            profile.role = role
            profile.status = "PENDING"
            profile.save()

        if role == "TUTOR":
            login(request, user)
            return redirect("tutor_onboarding")

        send_lexora_email(
            user.email,
            "مرحبًا بك في Lexora",
            f"""
            <div style="font-family: Arial; direction: rtl; text-align: right;">
                <h2>مرحبًا {user.username} 👋</h2>
                <p>تم إنشاء حسابك في Lexora بنجاح.</p>
                <p>يمكنك الآن تسجيل الدخول والبدء في حجز الدروس مع المعلمين.</p>
                <p>شكرًا لانضمامك إلينا.</p>
            </div>
            """
        )

        messages.success(request, "تم إنشاء الحساب بنجاح. يمكنك تسجيل الدخول الآن.")
        return redirect("login")

    return render(request, "accounts/register.html")


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "بيانات الدخول غير صحيحة.")
            return redirect("login")

        login(request, user)
        return redirect("home")

    return render(request, "accounts/login.html")


def user_logout(request):
    logout(request)
    return redirect("home")


@login_required
def tutor_onboarding(request):
    profile = Profile.objects.filter(user=request.user).first()
    if profile is None:
        profile = Profile.objects.create(
            user=request.user,
            role="TUTOR",
            status="PENDING"
        )

    if profile.role != "TUTOR":
        return redirect("home")

    tutor = Tutor.objects.filter(user=request.user).first()

    if request.method == "POST":
        name = (request.POST.get("name", "") or "").strip() or request.user.username
        language = (request.POST.get("language", "") or "").strip()
        country = (request.POST.get("country", "") or "").strip()
        bio = (request.POST.get("bio", "") or "").strip()

        price_raw = (request.POST.get("price", "") or "").strip()
        try:
            price = int(price_raw)
        except ValueError:
            price = 0

        cv = request.FILES.get("cv")

        if not language or not country or price <= 0:
            messages.error(request, "تأكدي من إدخال اللغة والدولة والسعر بشكل صحيح.")
            return redirect("tutor_onboarding")

        if not cv and not profile.cv:
            messages.error(request, "الرجاء رفع السيرة الذاتية (CV).")
            return redirect("tutor_onboarding")

        if tutor is None:
            tutor = Tutor(user=request.user)

        tutor.name = name
        tutor.language = language
        tutor.country = country
        tutor.price = price
        tutor.bio = bio
        tutor.rating = 4.8
        tutor.is_active = True
        tutor.save()

        if cv:
            profile.cv = cv

        profile.status = "PENDING"
        profile.save()

        send_lexora_email(
            request.user.email,
            "تم استلام طلبك كمعلم في Lexora",
            f"""
            <div style="font-family: Arial; direction: rtl; text-align: right;">
                <h2>مرحبًا {request.user.username} 👋</h2>
                <p>تم استلام طلبك للانضمام كمعلم في Lexora.</p>
                <p>طلبك الآن قيد المراجعة من الإدارة.</p>
                <p>سنقوم بتحديث حالة طلبك داخل الموقع عند الانتهاء من المراجعة.</p>
            </div>
            """
        )

        messages.success(request, "تم إرسال ملفك بنجاح وهو الآن قيد المراجعة ✅")
        return redirect("home")

    return render(request, "accounts/tutor_onboarding.html", {"tutor": tutor})
```
