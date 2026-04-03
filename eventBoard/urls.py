"""
URL configuration for eventBoard project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from schedule import views as schedule_views

urlpatterns = [
    path("", RedirectView.as_view(url="board/")),
    path("admin/", admin.site.urls),
    path("board/", include("schedule.urls")),
    path("schedule/", schedule_views.schedule_compact, name="schedule_compact"),
    path("schedule/<int:slot_id>/", schedule_views.slot_detail, name="slot_detail"),
    path("registrations/", schedule_views.registrations_list, name="registrations_list"),
    path("registrations/<int:registration_id>/", schedule_views.registration_detail, name="registration_detail"),
]
