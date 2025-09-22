from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from main.models import StudentProfile, Marks, SeatAllocation ,Notification
from .utils import rank_and_allocate
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.contrib import messages
from .forms import AdminSignupForm
from django.shortcuts import render, get_object_or_404
from django.utils.safestring import mark_safe
from .models import Branch,FeeReceipt
from .utils import send_allocation_notifications
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from .models import AdminOTP
import random
from django.core.mail import send_mail
from datetime import timedelta
from django.contrib.auth import get_backends
from .models import AdminProfile
from main.utils import send_password_reset_otp


from main.models import PasswordResetOTP 
# Create your views here.
print("LOADED ADMIN SECRET:", getattr(settings, 'ADMIN_SECRET_KEY', '❌ NOT FOUND'))
 

def admin_login_redirect(request):
    return redirect('admin_home') 

def verify_admin_key(request):
    if request.method == 'POST':
        key = request.POST.get('secret_key')
        print("Received key:", key)
        if key == settings.ADMIN_SECRET_KEY:
            request.session['admin_pin_verified']=True
            return JsonResponse({'status': 'ok'})
          
        else:
            return JsonResponse({'status': 'fail'})

@login_required
def social_redirect(request):
    user = request.user
    if request.session.get('admin_pin_verified'):
        request.session['is_verified_admin'] = True  # ✅ Set verified flag
        request.session['admin_pin_verified'] = False  
        print("Session:", request.session.items())

        user.is_staff = True
        
        user.save()

       
        return redirect('admin_dashboard')

    # Default to student
    return redirect('student_dashboard')

def admin_home(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard') 
    return render(request, 'adminpanel/admin_home.html') 

       
def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)

            # ✅ Check database verification status
            try:
                profile = AdminProfile.objects.get(user=user)
                if profile.is_verified:
                    request.session['is_verified_admin'] = True
                    return redirect('admin_dashboard')
                else:
                    messages.error(request, "Please verify your email before accessing dashboard.")
                    logout(request)
                    return redirect('admin_home')
            except AdminProfile.DoesNotExist:
             # ✅ Auto-create profile if missing
                 profile = AdminProfile.objects.create(user=user, is_verified=True)
                 request.session['is_verified_admin'] = True
                 return redirect('admin_dashboard')


        else:
            messages.error(request, "Invalid credentials or not an admin.")
            return redirect('admin_login')  # 👈 cleaned error part
    return render(request, 'adminpanel/admin_login.html')





def admin_signup_view(request):
    if request.method == 'POST':
        form = AdminSignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_staff = True
            user.is_active = False  # ✅ Block login until OTP verified
            user.save()

            # ✅ Generate and save OTP
            otp = str(random.randint(100000, 999999))
            AdminOTP.objects.update_or_create(user=user, defaults={
                'otp_code': otp,
                'created_at': timezone.now()
            })

            # ✅ Send email
            send_mail(
                subject="Verify Your Admin Email",
                message=f"Your OTP for admin verification is: {otp}",
                from_email="studentcounselingproject@gmail.com",
                recipient_list=[user.email],
                fail_silently=False,
            )

            # ✅ Save user ID to session for OTP verification
            request.session['temp_admin_id'] = user.id

            messages.success(request, "Admin account created! Please check your email for the OTP.")
            return redirect('verify_admin_otp')  # 👈 Redirect to OTP verification
    else:
        form = AdminSignupForm()

    return render(request, 'adminpanel/admin_signup.html', {'form': form})

def verify_admin_otp(request):
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        user_id = request.session.get('temp_admin_id')

        if not user_id:
            messages.error(request, "Session expired. Please register again.")
            return redirect('admin_signup')

        user = User.objects.get(id=user_id)
        admin_otp = AdminOTP.objects.get(user=user)

        # Check if OTP expired (10 minutes)
        if timezone.now() > admin_otp.created_at + timedelta(minutes=10):
            user.delete()
            admin_otp.delete()
            messages.error(request, "OTP expired. Please register again.")
            return redirect('admin_signup')

        if otp_input == admin_otp.otp_code:
            user.is_active = True
            # user.is_staff=True
            user.save()
            AdminProfile.objects.update_or_create(user=user, defaults={'is_verified': True})
            admin_otp.delete()
            # ✅ Explicit backend needed if using multiple
            user.backend = get_backends()[0].__module__ + '.' + get_backends()[0].__class__.__name__
            login(request, user)

            if user.is_staff:
                request.session['is_verified_admin'] = True 
                return redirect('admin_dashboard')
            else:
                return redirect('student_dashboard')
            
        else:
            return render(request, 'adminpanel/verify_admin_otp.html', {'error': 'Incorrect OTP'})
    return render(request, 'adminpanel/verify_admin_otp.html')

def admin_logout(request):
    logout(request)
    request.session.flush()  
    return redirect('home')


@login_required(login_url='admin_login')
def admin_dashboard(request):
    if not request.session.get('is_verified_admin'):
        return redirect('home') 

    students = StudentProfile.objects.all()  # Get all registered students

    student_data = []
    for student in students:
        try:
            allocation = SeatAllocation.objects.get(student=student)
            rank = allocation.rank if allocation.rank else "❌ Not Allotted"
            branch = allocation.allocated_branch if allocation.allocated_branch else "❌ Not Allotted"
            fee_receipt = allocation.fee_receipt.url if allocation.fee_receipt else None
            is_verified = allocation.is_verified
        except SeatAllocation.DoesNotExist:
            rank = "❌ Not Allotted"
            branch = "❌ Not Allotted"
            fee_receipt = None
            is_verified = False
        student_data.append({
            'id': student.id,
            'name': student.full_name,
            'email': student.profile_email,
            'phone': student.phone,
            'status': student.verification_status,
            'rank': rank,
            'allocated_branch': branch,
            'receipt': fee_receipt,
            'receipt_verified': is_verified,
        })
        
    branches = Branch.objects.all()
    return render(request, 'adminpanel/admin_dashboard.html', {
        'students': student_data,
        'branches': branches,
    })



@login_required(login_url='admin_login')
def view_student(request, id):
    student = get_object_or_404(StudentProfile, id=id)
    marks = Marks.objects.filter(student=student).first()

    # Calculate % if marks exist
    if marks:
        tenth_total = (
            marks.highschool_math + marks.highschool_science +
            marks.highschool_social_science + marks.highschool_english + marks.highschool_hindi
        )
        tenth_percent = round(tenth_total / 500 * 100, 2)

        twelfth_total = (
            marks.plus2_physics + marks.plus2_chemistry + marks.plus2_math
        )
        twelfth_percent = round(twelfth_total / 300 * 100, 2)
    else:
        tenth_percent = "N/A"
        twelfth_percent = "N/A"

    return render(request, 'adminpanel/student_view.html', {
        'student': student,
        'marks': marks,
        'tenth_percent': tenth_percent,
        'twelfth_percent': twelfth_percent,
    })




@login_required(login_url='admin_login')
def verify_student(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        action = request.POST.get('action')

        try:
            student = StudentProfile.objects.get(id=student_id)
        except StudentProfile.DoesNotExist:
            return HttpResponse("Student not found", status=404)

        if action == 'approve':
            student.verification_status = 'Approved'
            student.save()

            Notification.objects.create(
                student=student.user,
                message="✅ Your information has been approved."
            )

        elif action == 'reject':
      
            Notification.objects.create(
                  student=student.user,
                 message=mark_safe(" ❌ Your submitted data was rejected due to incorrect information.Kindly resubmit your details by filling the form again after refreshing the page or re-logging in.")

            )

            Marks.objects.filter(student=student).delete()
            student.delete()


        return redirect('admin_dashboard')
    
    return HttpResponse("Invalid request method", status=405)

@login_required(login_url='admin_login')
def run_allocation_view(request):
    if request.method == 'POST':
        rank_and_allocate()
        messages.success(request, "✅ Seat allocation completed!")
        return redirect('admin_dashboard')
    else:
        return HttpResponse("Invalid request method", status=405)
    

@staff_member_required
def send_notifications_view(request):
    send_allocation_notifications()
    messages.success(request, "✅ Notifications sent to all students.")
    return redirect('admin_dashboard')




@require_POST
@login_required(login_url='admin_login')
def approve_receipt(request, id):
    student = get_object_or_404(StudentProfile, id=id)

    try:
        allocation = SeatAllocation.objects.get(student=student)
        allocation.is_verified = True
        allocation.save()

        student.seat_allocated = True
        student.notification_seen = False  # So they get a new notification on dashboard
        student.save()
         
        try:
            fee_receipt = FeeReceipt.objects.get(student=student)
            fee_receipt.is_approved = True
            fee_receipt.save()
        except FeeReceipt.DoesNotExist:
            pass 


        Notification.objects.create(
            student=student.user,
            message="✅ Your fee has been verified and your seat has been confirmed. kindly download the offer letter"
        )

        messages.success(request, f"✅ Receipt approved for {student.user.username}.")
    except SeatAllocation.DoesNotExist:
        messages.error(request, "Seat allocation not found.")
    return redirect('admin_dashboard')
# utils.py is already shared by both student + admin

def admin_forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email").strip().lower()
        try:
            user = User.objects.get(email=email, is_staff=True)
            send_password_reset_otp(user)

            request.session['reset_email'] = email
            messages.success(request, "An OTP has been sent to your email.")
            return redirect("admin_verify_otp")
        except User.DoesNotExist:
            messages.error(request, "This admin email is not registered.")
    return render(request, "adminpanel/forgot_password.html")


def admin_verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        email = request.session.get('reset_email')

        print("Entered OTP:", entered_otp)
        print("Session email:", email)

        if not email:
            messages.error(request, "Your session expired. Please request a new OTP.")
            return redirect("admin_forgot_password")

        try:
            user = User.objects.get(email=email, is_staff=True)
            otp_obj = PasswordResetOTP.objects.filter(user=user).last()
            print("DB OTP:", otp_obj.otp if otp_obj else None)
        except User.DoesNotExist:
            messages.error(request, "Invalid session user.")
            return redirect("admin_forgot_password")

        if otp_obj and str(otp_obj.otp) == entered_otp:
            request.session['otp_verified'] = True
            return redirect("admin_reset_password")
        else:
            messages.error(request, "Invalid OTP.")
    return render(request, "adminpanel/verify_otp.html")


def admin_reset_password(request):
    if request.method == "POST":
        new_pass = request.POST.get("password")
        confirm_pass = request.POST.get("confirm_password")

        if new_pass == confirm_pass:
            email = request.session.get('reset_email')
            if request.session.get('otp_verified'):
                try:
                    user = User.objects.get(email=email, is_staff=True)
                    user.set_password(new_pass)
                    user.save(update_fields=["password"])

                    # cleanup session
                    request.session.pop('reset_email', None)
                    request.session.pop('otp_verified', None)

                    messages.success(request, "Password reset successful. Please login.")
                    return redirect("admin_login")
                except User.DoesNotExist:
                    messages.error(request, "Something went wrong. Try again.")
            else:
                messages.error(request, "OTP not verified.")
        else:
            messages.error(request, "Passwords do not match.")
    return render(request, "adminpanel/reset_password.html")
