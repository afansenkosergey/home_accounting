from django.urls import path, include
from accounts import views

urlpatterns = [
    path('login/', views.log_in, name='log_in'),
    path('signup/', views.registration, name='signup'),
    path('logout/', views.logout_page, name='logout'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),
]
