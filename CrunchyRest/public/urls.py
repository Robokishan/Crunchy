from django.urls import path
from public import views
from public.views import CompaniesListView
from public.views import SettingsList

urlpatterns = [
    path('comp', CompaniesListView.as_view()),
    path('connection', views.connection),
    path('settings', SettingsList.as_view()),
]
