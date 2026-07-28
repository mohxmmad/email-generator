from django.urls import path

from .views import GenerateEmailView, HealthCheckView


urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("generate-email/", GenerateEmailView.as_view(), name="generate-email"),
]
