from django.contrib import admin
from .models import Branch
from .models import SiteSetting,FeeReceipt,AdminProfile

class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_seats', 'filled_seats')
    list_editable = ('total_seats',)  # Makes 'total_seats' editable from the list view

admin.site.register(Branch, BranchAdmin)

admin.site.register(SiteSetting)

models_to_register = [FeeReceipt, AdminProfile]

for model in models_to_register:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass