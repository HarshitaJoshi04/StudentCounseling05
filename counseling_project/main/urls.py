from django.urls import path
from . import views



urlpatterns = [
    path('', views.student_home, name="student_home"),
    path('register/', views.student_register, name='student_register'),
    path('login/', views.student_login, name='student_login'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('logout/', views.student_logout, name='student_logout'),
    path('notifications/', views.notification_page, name='student_notifications'),
    path('upload-fee-receipt/', views.upload_fee_receipt, name='upload_fee_receipt'),
    path('download-offer-letter/', views.download_offer_letter, name='download_offer_letter'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
        # Forgot Password for Student
    path('student/forgot-password/', views.student_forgot_password, name='student_forgot_password'),
    path('student/verify-otp/', views.student_verify_otp, name='student_verify_otp'),
    path('student/reset-password/', views.student_reset_password, name='student_reset_password'),
]
