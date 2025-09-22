from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import StudentProfileForm, MarksForm,StudentRegisterForm
from .models import StudentProfile , Marks,Notification,SeatAllocation
from adminpanel.models import SiteSetting,FeeReceipt
from django.shortcuts import render, get_object_or_404
from adminpanel.utils import generate_offer_letter
import random
from django.core.mail import send_mail
from .models import UserOTP
from django.contrib.auth import get_backends
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponseForbidden
from django.conf import settings
from .models import PasswordResetOTP


from .utils import send_password_reset_otp
#  Home Page
def home(request):
    return render(request, 'home.html')

def student_home(request):
    if request.user.is_authenticated:
        return redirect('student_dashboard')  # ✅ Redirect ensures proper context
    else:
        return render(request, 'main/student_home.html')

  
# ✅ Student Register View
def student_register(request):
    if request.method == 'POST':
        form=StudentRegisterForm(request.POST)
        email = request.POST.get('email')

        if StudentProfile.objects.filter(user__email=email).exists():

            request.session['email_exists'] = True
            return redirect('student_register')
        

        if form.is_valid():
            user=form.save(commit=False)
            full_name=form.cleaned_data.get('full_name')
            password=form.cleaned_data.get('password')
            user.set_password(password)
            name_parts = full_name.split()
            user.first_name = name_parts[0]
            user.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ''
           

           
            user.is_active = False  # ✅ Prevent login before email verification
            user.save()
            
                        # ✅ Create OTP and send it to email
            otp = str(random.randint(100000, 999999))
            UserOTP.objects.update_or_create(user=user, defaults={'otp': otp})
            send_mail(
                subject="Your Email Verification OTP",
                message=f"Your OTP is {otp}. Please do not share it.",
                from_email="settings.EMAIL_HOST_USER",  # same as EMAIL_HOST_USER in settings.py
                recipient_list=[user.email],
                fail_silently=False,
            )

            # ✅ Save user ID in session to verify later
            request.session['temp_user_id'] = user.id

            messages.success(request, "Please enter otp to verify")
            return redirect('verify_otp')
        else:
            messages.error(request, "Please correct the errors below.")
            return render(request, 'main/register.html', {'form': form}) 
    else:
        form = StudentRegisterForm()

    email_exists = request.session.pop('email_exists', False)

    return render(request, 'main/register.html', {
        'form': form,
        'email_exists': email_exists
    })

def verify_otp(request):
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        user_id = request.session.get('temp_user_id')

        if not user_id:
            return redirect('student_register')

        user = User.objects.get(id=user_id)
        user_otp = UserOTP.objects.get(user=user)
        
               
               
         # ✅ Expiry logic: 10 minutes
        if timezone.now() > user_otp.created_at + timedelta(minutes=10):
            user_otp.delete()
            user.delete() 
            messages.error(request, "OTP expired. Please register again.")
            return redirect('student_register')


        if otp_input == user_otp.otp:
            user_otp.delete()
            user.is_active = True 
            user.save()
            user.backend = get_backends()[0].__class__.__module__ + '.' + get_backends()[0].__class__.__name__
            login(request, user) 
            return redirect('student_dashboard') 

        else:
            return render(request, 'main/verify_otp.html', {'error': 'Incorrect OTP'})

    return render(request, 'main/verify_otp.html')



# ✅ Student Login View
def student_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user and user.check_password(password):
            if not user.is_active:
              messages.error(request, "Please verify your email before logging in.")
              return redirect('student_login')
        if user is not None:
            if user.is_staff:
                messages.error(request, "Admins are not allowed to log in here. Please use the Admin Login page.")
                return redirect('student_login')
            print("✅ Logged in:", user.username)  
            login(request, user)
            return redirect('student_dashboard') 
        else:
            messages.error(request, "Invalid credentials.")

    return render(request, 'main/login.html')

def generate_otp():
    return str(random.randint(100000, 999999))

# this fun is not used
def send_otp_email(email, otp):
    subject = 'Your Email Verification OTP'
    message = f'Your OTP is {otp}. Please enter it to complete your signup.'
    from_email =  settings.EMAIL_HOST_USER
    send_mail(subject, message, from_email, [email])

# ✅ Student Dashboard
@login_required(login_url='student_login')
def student_dashboard(request):
   
    user = request.user

    if request.user.is_staff:
        return render(request, 'main/access_denied.html', {
            'message': "⚠️ Access Denied: Admins are not allowed to access the student dashboard."
        })
    
    #  Check site setting
    site_setting = SiteSetting.objects.first()
    registration_open = site_setting.is_registration_open if site_setting else False

    #  Try to get profile if exists
    profile = StudentProfile.objects.filter(user=user).first()
    already_filled = False
    show_notification = False
    marks = None
    allocation = None

    if profile:
        try:
            marks = Marks.objects.get(student=profile)
            already_filled = True

            try:
                allocation = SeatAllocation.objects.get(student=profile)
            except SeatAllocation.DoesNotExist:
                allocation = None

            if profile.seat_allocated and not profile.notification_seen:
                show_notification = True
                profile.notification_seen = True
                profile.save()
        except Marks.DoesNotExist:
            pass

    if request.method == 'POST' and not already_filled and registration_open:
        profile_form = StudentProfileForm(request.POST, request.FILES)
        marks_form = MarksForm(request.POST)
        if profile_form.is_valid() and marks_form.is_valid():
            profile_obj = profile_form.save(commit=False)
            profile_obj.user = user
            profile_obj.save()

            marks_obj = marks_form.save(commit=False)
            marks_obj.student = profile_obj
            marks_obj.save()

            messages.success(request, "Information submitted successfully")
            return redirect('student_dashboard')
    elif not already_filled and registration_open:
        profile_form = StudentProfileForm()
        marks_form = MarksForm()
    else:
        profile_form = None
        marks_form = None

    # Fetch notifications
    notifications = Notification.objects.filter(student=user).order_by('seen', '-created_at')
    unread_count = notifications.filter(seen=False).count()

    return render(request, 'main/student_dashboard.html', {
        'profile': profile,
        'profile_form': profile_form,
        'marks_form': marks_form,
        'already_filled': already_filled,
        'marks': marks,
        'registration_open': registration_open,
        'show_notification': show_notification,
        'notifications': notifications,
        'unread_count': unread_count,
        'allocation': allocation, 
    })

#  Logout View
def student_logout(request):
    logout(request)
    return redirect('student_home')

def notification_page(request):
   #  First update DB
    Notification.objects.filter(student=request.user, seen=False).update(seen=True)

#  Then re-fetch from DB with updated values
    notifications = Notification.objects.filter(student=request.user).order_by('-created_at')
    
    return render(request, 'main/notification.html', {
        'notifications': notifications,
    })


  # imported from adminpanel.models

@login_required(login_url='student_login')
def upload_fee_receipt(request):
    user = request.user
    try:
        profile = StudentProfile.objects.get(user=user)
        allocation = SeatAllocation.objects.get(student=profile)
    except (StudentProfile.DoesNotExist, SeatAllocation.DoesNotExist):
        messages.error(request, "❌ Seat allocation not found.")
        return redirect('student_dashboard')

    if request.method == 'POST' and request.FILES.get('receipt'):
        uploaded_file = request.FILES['receipt']
        allocation.fee_receipt =  uploaded_file
        allocation.is_verified = False  # Admin approves later
        allocation.save()

        FeeReceipt.objects.update_or_create(
                student=profile,
                defaults={'receipt': uploaded_file,'is_approved': False}
               
            )

        #  Update StudentProfile status (optional)
        profile.seat_allocated = True
        profile.save()

        messages.success(request, "✅ Receipt uploaded successfully.")
    else:
        messages.error(request, "❌ No receipt file found.")

    return redirect('student_dashboard')


@login_required(login_url='student_login')
def download_offer_letter(request):
    student = get_object_or_404(StudentProfile, user=request.user)

    try:
        allocation = SeatAllocation.objects.get(student=student)

        # Only allow download if admin has approved the seat
        if not allocation.is_verified:
            messages.error(request, "❌ Your seat is not verified yet.")
            return redirect('student_dashboard')

    except SeatAllocation.DoesNotExist:
        messages.error(request, "❌ You don't have a seat allocation yet.")
        return redirect('student_dashboard')

    return generate_offer_letter(student)


def student_forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email").strip().lower()

        try:
            user = User.objects.get(email=email, is_staff=False)  # student only
            send_password_reset_otp(user)  # send OTP

            # save email in session for later OTP verification
            request.session['reset_email'] = email  

            messages.success(request, "An OTP has been sent to your email.")
            return redirect("student_verify_otp")  # correct name
        except User.DoesNotExist:
            messages.error(request, "This email is not registered.")

    return render(request, "main/forgot_password.html")


def student_verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        email = request.session.get('reset_email')
        print("Entered OTP:", entered_otp)
        print("Session email:", email)

        if not email:
            messages.error(request, "Session expired. Try again.")
            return redirect("student_forgot_password")

        try:
            user = User.objects.get(email=email, is_staff=False)
            otp_obj = PasswordResetOTP.objects.filter(user=user).last()  # ✅ FIX
            print("DB OTP:", otp_obj.otp if otp_obj else None)
        except User.DoesNotExist:
            messages.error(request, "Invalid session user.")
            return redirect("student_forgot_password")

        if otp_obj and str(otp_obj.otp) == entered_otp:
            request.session['otp_verified'] = True
            return redirect("student_reset_password")
        else:
            messages.error(request, "Invalid OTP.")
    return render(request, "main/verify_otp1.html")


def student_reset_password(request):
    if request.method == "POST":
        new_pass = request.POST.get("password")
        confirm_pass = request.POST.get("confirm_password")

        if new_pass == confirm_pass:
            email = request.session.get('reset_email')
            if request.session.get('otp_verified'):
                try:
                    user = User.objects.get(email=email, is_staff=False)
                    user.set_password(new_pass)
                    user.save()

                    # cleanup session and OTP
                    request.session.pop('reset_email', None)
                    request.session.pop('otp_verified', None)
                    PasswordResetOTP.objects.filter(user=user).delete()

                    messages.success(request, "Password reset successful. Login now.")
                    return redirect("student_login")
                except User.DoesNotExist:
                    messages.error(request, "Something went wrong. Try again.")
            else:
                messages.error(request, "OTP not verified.")
        else:
            messages.error(request, "Passwords do not match.")

    return render(request, "main/reset_password.html")