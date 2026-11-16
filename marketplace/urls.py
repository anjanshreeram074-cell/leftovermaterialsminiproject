from django.urls import path
from . import views, views_api, api_views

urlpatterns = [
    # Web views
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

    # API endpoints (for Vercel proxy)
    path('api/listings/', api_views.api_listings, name='api_listings'),
    path('api/listings/<int:pk>/', api_views.api_listing_detail, name='api_listing_detail'),
    path('api/listings/create/', api_views.api_create_listing, name='api_create_listing'),
    path('api/listings/<int:pk>/update/', api_views.api_update_listing, name='api_update_listing'),
    path('api/listings/<int:pk>/delete/', api_views.api_delete_listing, name='api_delete_listing'),
    path('api/listings/<int:pk>/sold/', api_views.api_mark_sold, name='api_mark_sold'),
    path('api/my-listings/', api_views.api_my_listings, name='api_my_listings'),
    path('api/calculator/estimate/', api_views.api_calculator_estimate, name='api_calculator_estimate'),
]