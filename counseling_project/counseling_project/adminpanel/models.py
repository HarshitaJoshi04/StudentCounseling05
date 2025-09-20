from django.db import models
from main.models import StudentProfile
from django.utils import timezone
from django.contrib.auth.models import User 
# Create your models here.
class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True)
    total_seats = models.PositiveIntegerField()
    filled_seats = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

class SiteSetting(models.Model):
    is_registration_open = models.BooleanField(default=True)

    def __str__(self):
        return "Site Setting"
    



class FeeReceipt(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE)
    receipt = models.FileField(upload_to='fee_receipts/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.full_name} - Fee Receipt"
    

class AdminOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"OTP for {self.user.username}"
    

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - Verified: {self.is_verified}"