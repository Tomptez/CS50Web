from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("wiki/newpage", views.newpage, name="newpage"),
    path("wiki/randompage", views.randompage, name="randompage"),
    path("wiki/<str:title>", views.entry, name="entry"),
    path("edit/<str:title>", views.editpage, name="editpage")
]
