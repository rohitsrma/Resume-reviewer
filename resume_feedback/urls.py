from django.urls import path, include
from resume_feedback import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api', views.upload_pdf, name='api')
]