from django.contrib import admin
from .models import StudentProfile, Marks, SeatAllocation
from .models import Notification
# Register your models here.

admin.site.register(StudentProfile)
admin.site.register(Marks)
admin.site.register(SeatAllocation)
admin.site.register(Notification)