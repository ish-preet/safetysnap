from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload', views.upload, name='upload'),
    path('history', views.history, name='history'),
    path('result/<int:id>', views.result, name='result'),
    path('analytics', views.analytics, name='analytics'),
]