from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class StudentProfile(models.Model):
    user=models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100) 
    phone=models.CharField(max_length=15)
    address=models.TextField()
    dob=models.DateField()
    branch1=models.CharField(max_length=100, choices=[('CSE', 'CSE'), ('ECE', 'ECE')], null=True)
    branch2=models.CharField(max_length=100,choices=[('CSE', 'CSE'), ('ECE', 'ECE'),], null=True)
    aadhar_file = models.FileField(upload_to='aadhaar_uploads/', blank=True, null=True)
    aadhaar_number = models.CharField(max_length=12, blank=True)
    profile_picture = models.ImageField(upload_to='avatars/', default='avatars/default-avatar.png')
    tenth_result = models.FileField(upload_to='results/10th/', blank=True, null=True)
    twelfth_result = models.FileField(upload_to='results/12th/', blank=True, null=True)
    profile_email = models.EmailField(blank=True) 
    is_verified_by_admin = models.BooleanField(default=False)
    verification_status = models.CharField( max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],default='Pending')
    admin_remark = models.TextField(blank=True, null=True)
    branch_allotted = models.CharField(max_length=100, null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    seat_allocated = models.BooleanField(default=False)
    notification_seen = models.BooleanField(default=False) 
    def __str__(self):
        return self.user.username

class Marks(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE)
    highschool_math = models.IntegerField(default=0)
    highschool_science = models.IntegerField(default=0)
    highschool_social_science = models.IntegerField(default=0)
    highschool_english = models.IntegerField(default=0)
    highschool_hindi = models.IntegerField(default=0)
    plus2_physics = models.IntegerField(default=0)
    plus2_chemistry = models.IntegerField(default=0)
    plus2_math = models.IntegerField(default=0)

    def total_12th(self):
        return self.plus2_physics + self.plus2_chemistry + self.plus2_math

    def __str__(self):
        return f"Marks of {self.student.user.username}"
    
class SeatAllocation(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE)
    allocated_branch = models.CharField(max_length=100, blank=True, null=True)
    rank = models.IntegerField(blank=True, null=True)  
    is_accepted = models.BooleanField(default=False)
    fee_receipt = models.ImageField(upload_to='receipts/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.user.username} - {self.allocated_branch}"
    

    
class Notification(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} - {self.message[:30]}"


class UserOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.otp}"


    
class PasswordResetOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.username}"