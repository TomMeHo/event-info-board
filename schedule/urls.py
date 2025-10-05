from django.urls import path
from . import views

urlpatterns = [
    path("", views.event_board, name="event_board"),
]