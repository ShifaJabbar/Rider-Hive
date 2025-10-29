# © https://github.com/MrMKN
# Full Stacked By Mr MKN

from django.contrib import admin
from .models import *

@admin.register(Owner)
class Owner(admin.ModelAdmin):
    # readonly_fields = ('id',)
    list_display = ('name', 'email', 'phone', 'car_name', 'car_number')

    def get_list_display_links(self, request, list_display):
        return list_display

@admin.register(Rider)
class Rider(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'cash')

    def get_list_display_links(self, request, list_display):
        return list_display

@admin.register(Trip)
class Trip(admin.ModelAdmin):
    def name(self, obj):
        return obj.owner.name  
    
    name.short_description = 'Owner'
    list_display = ('name', 'start_date', 'origin', 'destination', 'status', 'is_booked', 'seats')

    def get_list_display_links(self, request, list_display):
        return list_display
    
@admin.register(Booking)
class Booking(admin.ModelAdmin):
    def owner(self, obj):
        return obj.trip.owner.name  
    
    def rider(self, obj):
        return obj.rider.name 
    
    owner.short_description = 'Owner'
    rider.short_description = 'Rider'
    list_display = ('owner', 'rider', 'is_done')

    def get_list_display_links(self, request, list_display):
        return list_display