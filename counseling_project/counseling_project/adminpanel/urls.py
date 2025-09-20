from django.urls import path
from . import views
urlpatterns = [
    path('', views.admin_login_redirect, name='adminpanel_root'), 
    path('home/', views.admin_home, name="admin_home"),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('signup/', views.admin_signup_view, name='admin_signup'),
    path('verify/', views.verify_student, name='verify_student'),
    path('verify-key/', views.verify_admin_key, name='verify_admin_key'),
    path('run-allocation/', views.run_allocation_view, name='run_allocation'),
    path('send-notifications/', views.send_notifications_view, name='send_notifications'),
    path('social-redirect/', views.social_redirect, name='social_redirect'),
    path('student/<int:id>/view/', views.view_student, name='view_student'),
    path('verify-admin-otp/', views.verify_admin_otp, name='verify_admin_otp'),
    path('approve-receipt/<int:id>/', views.approve_receipt, name='approve_receipt'),
]
