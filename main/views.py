import stripe

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt

from accounts.views import send_lexora_email
from .models import Tutor, Booking

stripe.api_key = settings.STRIPE_SECRET_KEY


def home(request):
    application_status = None
    admin_note = None

    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        if profile and profile.role == "TUTOR":
            application_status = profile.status
            admin_note = profile.admin_note

    return render(request, "main/home.html", {
        "application_status": application_status,
        "admin_note": admin_note,
    })


def robots_txt(request):
    content = """User-agent: *
Allow: /

Sitemap: https://lexoraapp.com/sitemap.xml
"""
    return HttpResponse(content, content_type="text/plain")


def tutors_list(request):
    tutors = Tutor.objects.filter(
        is_active=True,
        user__profile__status="APPROVED"
    ).order_by("-rating", "price")

    return render(request, "main/tutors_list.html", {"tutors": tutors})


def tutor_profile(request, tutor_id):
    tutor = get_object_or_404(Tutor, id=tutor_id, is_active=True)
    return render(request, "main/tutor_profile.html", {"tutor": tutor})


@login_required
def book_lesson(request, tutor_id):
    tutor = get_object_or_404(Tutor, id=tutor_id, is_active=True)

    if request.method == "POST":
        lesson_date = request.POST.get("lesson_date")
        lesson_time = request.POST.get("lesson_time")
        note = request.POST.get("note", "")

        amount = float(tutor.price)
        platform_fee = round(amount * 0.20, 2)
        tutor_earnings = round(amount - platform_fee, 2)

        booking = Booking.objects.create(
            student=request.user,
            tutor=tutor,
            lesson_date=lesson_date,
            lesson_time=lesson_time,
            note=note,
            amount=amount,
            platform_fee=platform_fee,
            tutor_earnings=tutor_earnings,
            currency="USD",
            is_paid=False,
        )

        student_email = request.user.email
        tutor_email = tutor.user.email if tutor.user else ""

        if student_email:
            send_lexora_email(
                student_email,
                "تم إنشاء حجزك في Lexora",
                f"""
                <div style="font-family: Arial; direction: rtl; text-align: right;">
                    <h2>تم إنشاء حجزك بنجاح ✅</h2>
                    <p>مرحبًا {request.user.username}،</p>
                    <p>تم إنشاء حجزك مع المعلم <strong>{tutor.name}</strong>.</p>
                    <p><strong>تاريخ الدرس:</strong> {lesson_date}</p>
                    <p><strong>وقت الدرس:</strong> {lesson_time}</p>
                    <p><strong>المبلغ:</strong> {amount} USD</p>
                    <p>يرجى إكمال الدفع لتأكيد الحجز.</p>
                </div>
                """
            )

        if tutor_email:
            send_lexora_email(
                tutor_email,
                "لديك حجز جديد في Lexora",
                f"""
                <div style="font-family: Arial; direction: rtl; text-align: right;">
                    <h2>لديك حجز جديد 📚</h2>
                    <p>مرحبًا {tutor.name}،</p>
                    <p>قام الطالب <strong>{request.user.username}</strong> بإنشاء حجز جديد معك.</p>
                    <p><strong>تاريخ الدرس:</strong> {lesson_date}</p>
                    <p><strong>وقت الدرس:</strong> {lesson_time}</p>
                    <p><strong>ملاحظات الطالب:</strong> {note or "لا توجد ملاحظات"}</p>
                    <p>يرجى متابعة الحجز من لوحة التحكم أو صفحة الحجوزات.</p>
                </div>
                """
            )

        return redirect("checkout_booking", booking_id=booking.id)

    return render(request, "main/book_lesson.html", {"tutor": tutor})


@login_required
def checkout_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, student=request.user)

    if booking.is_paid:
        messages.info(request, "هذا الحجز مدفوع بالفعل.")
        return redirect("my_bookings")

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Lesson with {booking.tutor.name}",
                    },
                    "unit_amount": int(float(booking.amount) * 100),
                },
                "quantity": 1,
            }
        ],
        success_url=request.build_absolute_uri("/payment/success/"),
        cancel_url=request.build_absolute_uri(f"/tutors/{booking.tutor.id}/book/"),
        metadata={
            "booking_id": str(booking.id),
        },
        payment_intent_data={
            "metadata": {
                "booking_id": str(booking.id),
            }
        },
    )

    return redirect(session.url, code=303)


def payment_success(request):
    messages.success(request, "تم الدفع بنجاح ✅")
    return redirect("my_bookings")


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(student=request.user).order_by("-created_at")
    return render(request, "main/my_bookings.html", {"bookings": bookings})


@login_required
def delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, student=request.user)

    if request.method == "POST":
        booking.delete()
        messages.success(request, "تم حذف الحجز بنجاح 🗑️")

    return redirect("my_bookings")


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        booking_id = session.get("metadata", {}).get("booking_id")

        if booking_id:
            try:
                booking = Booking.objects.get(id=booking_id)
                booking.is_paid = True
                booking.save()
            except Booking.DoesNotExist:
                pass

    return HttpResponse(status=200)