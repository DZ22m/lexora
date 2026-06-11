from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Tutor


class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = "weekly"

    def items(self):
        return [
            "home",
            "tutors_list",
        ]

    def location(self, item):
        return reverse(item)


class TutorSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Tutor.objects.filter(is_active=True)

    def location(self, obj):
        return reverse("tutor_profile", args=[obj.id])

