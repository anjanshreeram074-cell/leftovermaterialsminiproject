from django.urls import path
from . import views, views_api

urlpatterns = [
    path('', views.home, name='home'),
    path('browse/', views.browse, name='browse'),
    path('sell/', views.sell, name='sell'),
    path('listing/<int:pk>/', views.detail, name='detail'),
    path('my-listings/', views.my_listings, name='my_listings'),
    path('edit/<int:pk>/', views.edit_listing, name='edit_listing'),
    path('delete/<int:pk>/', views.delete_listing, name='delete_listing'),
    path('sold/<int:pk>/', views.mark_sold, name='mark_sold'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('calculator/estimate/', views_api.calculate_estimate, name='calculate_estimate'),
]