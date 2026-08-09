from django.urls import path
from . import views

urlpatterns = [

    path(
        "",
        views.conversation_list,
        name="conversation_list",
    ),

    path("start/", views.start_conversation, name="start_conversation"),

    path(
        "<int:conversation_id>/",
        views.conversation_detail,
        name="conversation_detail",
    ),

    path(
        "start/<int:user_id>/",
        views.create_direct_conversation,
        name="create_direct_conversation",
    ),
]