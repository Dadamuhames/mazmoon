from django.urls import path, include
from . import views


urlpatterns = [
    path("static_infos", views.StaticInfView.as_view()),
    path("translations", views.TranslationsView.as_view()),
    path('languages', views.LangsList.as_view()),
    path("add_aplication", views.AddAplication.as_view()),
]