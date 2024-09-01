from django.urls import path
from public import views

urlpatterns = [
    path('comp', views.getCompanies),
    path('connection', views.connection),
]
