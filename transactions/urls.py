
from django.urls import path
from . import views


urlpatterns = [

    path(
        "<int:pk>/",
        views.payment_dashboard,
        name="payment_dashboard"
    ),

    path(
        "<int:pk>/round/<int:turn_id>/report/",
        views.report_payment,
        name="report_payment"
    ),

    path(
        "<int:pk>/payment/<int:payment_id>/review/",
        views.review_payment,
        name="review_payment"
    ),

]
