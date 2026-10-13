
from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create_jamiyah, name="create_jamiyah"),
    path("mine/", views.my_jamiyahs, name="my_jamiyahs"),
    path("explore/", views.explore_jamiyahs, name="explore_jamiyahs"),
    path("invite/<uuid:token>/", views.private_jamiyah_invite, name="private_jamiyah_invite"),
    path("<int:pk>/invite/regenerate/", views.regenerate_invite_link, name="regenerate_invite_link"),
    path("<int:pk>/edit/", views.edit_jamiyah, name="edit_jamiyah"),
    path("<int:pk>/cancel/", views.cancel_jamiyah, name="cancel_jamiyah"),
    path("<int:pk>/", views.jamiyah_detail, name="jamiyah_detail"),
    path("<int:pk>/join/", views.request_join, name="request_join"),
    path("<int:pk>/requests/<int:membership_id>/", views.manage_join_request, name="manage_join_request"),
    path("<int:pk>/schedule/generate/", views.generate_payout_schedule, name="generate_payout_schedule"),
    path("<int:pk>/delivery/", views.payout_delivery_dashboard, name="payout_delivery_dashboard"),
    path("<int:pk>/delivery/<int:turn_id>/confirm/", views.confirm_payout_delivery, name="confirm_payout_delivery"),
    path("<int:pk>/delivery/<int:turn_id>/seen/", views.mark_payout_delivery_seen, name="mark_payout_delivery_seen"),
    path("<int:pk>/completion/seen/",views.mark_jamiyah_completion_seen,name="mark_jamiyah_completion_seen"),
]
