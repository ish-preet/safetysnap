from django.urls import path
from . import views

urlpatterns = [
    path('test', views.api_test, name='api_test'),
    path('register', views.register, name='register'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('images', views.upload_image, name='upload_image'),
    path('images/', views.get_images, name='get_images'),
    path('images/<int:id>', views.get_image_detail, name='get_image_detail'),
    path('analytics', views.get_analytics, name='get_analytics'),
    path('labels', views.get_labels, name='get_labels'),
]