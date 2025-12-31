from django.urls import path
from . import views

urlpatterns = [
    path("apply/", views.apply_view, name="apply"),
    path("company/login/", views.company_login_view, name="company_login"),
    path("company/logout/", views.company_logout_view, name="company_logout"),
    path("company/applications/", views.company_applications_view, name="company_apps"),
    path("company/file/<int:file_id>/", views.company_download_file, name="company_download"),
]
