from django import views
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.homepage, name = "homepage"),
    path('homepage', views.homepage, name = "homepage"),
    path('signup', views.signup, name = "signup"),
    path('signin', views.signin, name = "signin"),
    path('signout', views.signout, name = "signout"),
    path('today', views.today, name = "today"),
    path('screeningTest', views.screeningTest, name = "screeningTest"),
    path('entries', views.entries, name='entries'),
    path('serve_file/<str:file_id>/', views.serve_file, name='serve_file'),
    path('adminDashboard/<str:selected_username>/', views.adminDashboard, name='adminDashboardWithUsername'),
    path('adminDashboard', views.adminDashboard, name='adminDashboard'),
    path('generic', views.generic, name = 'generic')

]
