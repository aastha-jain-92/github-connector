from django.urls import path, include

urlpatterns = [
    path("", include("connector.urls")),
]
