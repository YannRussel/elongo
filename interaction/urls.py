from django.urls import path
from . import views

app_name = "interaction"

urlpatterns = [
    path("", views.home, name="home"),

    path("enfants/nouveau/", views.enfant_create, name="enfant_create"),
    path("enfants/", views.enfant_list, name="enfant_list"),
    path("enfants/code/", views.enfant_lookup, name="enfant_lookup"),
    path("enfants/<str:code_enfant>/", views.enfant_detail, name="enfant_detail"),

    path(
        "enfants/<str:code_enfant>/rubrique/<int:rubrique_id>/evaluation/",
        views.evaluation_create,
        name="evaluation_create",
    ),

    path(
        "evaluation/resultat/<int:evaluation_id>/",
        views.evaluation_result,
        name="evaluation_result",
    ),
]