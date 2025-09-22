import random
from django.core.mail import send_mail
from django.conf import settings

def send_password_reset_otp(user):
    otp = str(random.randint(100000, 999999))  # 6 digit OTP

    # Save or update OTP in DB
    from .models import PasswordResetOTP
    PasswordResetOTP.objects.update_or_create(
        user=user, defaults={'otp': otp}
    )

    # Send OTP to email
    subject = "Password Reset OTP"
    message = f"Hello {user.username},\n\nYour OTP for resetting password is {otp}.\n\nEnter this in the website to reset your password."
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)
    return otp
