from django.urls import path
from public import views
from public.views import CompaniesListView
from public.views import SettingsList
from public.views import IndustryList

urlpatterns = [
    path('comp', CompaniesListView.as_view()),
    path('connection', views.connection),
    path('settings', SettingsList.as_view()),
    path('pending', views.PendingInQueue),
    path('industries', IndustryList.as_view()),
]
