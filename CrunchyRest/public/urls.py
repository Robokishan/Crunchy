from django.urls import path
from public import views
from public.views import CompaniesListView

urlpatterns = [
    path('comp', CompaniesListView.as_view()),
    path('connection', views.connection),
]
