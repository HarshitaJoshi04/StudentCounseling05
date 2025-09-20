from django import forms 
from .models import StudentProfile, Marks
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model=StudentProfile
        exclude=['user','submitted_at','branch_allotted', 'rank','seat_allocated','notification_seen','is_verified_by_admin','verification_status','admin_remark']
        widgets={
               'phone':forms.TextInput(attrs={
                'class':'form-control custom-input',
                'placeholder':'enter your phone number'
            }),
                 'dob':forms.TextInput(attrs={
                'class':'form-control custom-input',
                'placeholder':'yyyy-mm-dd'
            }),
                'branch1': forms.Select(attrs={
                'class': 'form-control custom-input'
            }),
                'branch2': forms.Select(attrs={
                'class': 'form-control custom-input'
            })
        }

    
    def clean(self):
        cleaned_data = super().clean()
        branch1 = cleaned_data.get('branch1')
        branch2 = cleaned_data.get('branch2')

        if branch1 and branch2 and branch1 == branch2:
            raise forms.ValidationError("Branch 1 and Branch 2 cannot be the same!")

        return cleaned_data
    

    def __init__(self, *args, **kwargs):
        super(StudentProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class MarksForm(forms.ModelForm):
    class Meta:
        model = Marks
        exclude = ['student']  
    
    
    def clean(self):
        cleaned_data = super().clean()

        subjects = [
            'highschool_math',
            'highschool_science',
            'highschool_social_science',
            'highschool_english',
            'highschool_hindi',
            'plus2_physics',
            'plus2_chemistry',
            'plus2_math',
        ]

        for subject in subjects:
            marks = cleaned_data.get(subject)
            if marks is not None and (marks < 0 or marks > 100):
                self.add_error(subject, f"{subject.replace('_', ' ').title()} must be between 0 and 100")

        return cleaned_data


    def __init__(self, *args, **kwargs):
        super(MarksForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class StudentRegisterForm(forms.ModelForm):
    full_name=forms.CharField(max_length=100, required=True,label="Full Name")
    password=forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    
    class Meta:
        model= User
        fields=['full_name', 'username', 'email', 'password', 'confirm_password']
        widgets={
            'username':forms.TextInput(attrs={'placeholder':'Username'}),
            'email':forms.EmailInput(attrs={'placeholder':'Email'}),
        }
   
    def clean(self):
        cleaned_data = super().clean()
        password=cleaned_data.get("password")
        confirm=cleaned_data.get("confirm_Password")
        
        if password and confirm and password!=confirm:
            raise ValidationError("Passwords do not match")
        
        return cleaned_data
    



