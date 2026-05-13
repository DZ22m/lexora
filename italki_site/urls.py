from django.contrib import admin
from django.urls import path, include
from main import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('tutors/', views.tutors_list, name='tutors_list'),
    path('tutors/<int:tutor_id>/', views.tutor_profile, name='tutor_profile'),
    path('tutors/<int:tutor_id>/book/', views.book_lesson, name='book_lesson'),
    path('booking/<int:booking_id>/checkout/', views.checkout_booking, name='checkout_booking'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('my-bookings/<int:booking_id>/delete/', views.delete_booking, name='delete_booking'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('accounts/', include('accounts.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)