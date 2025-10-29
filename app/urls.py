# © https://github.com/MrMKN
# Full Stacked By Mr MKN

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashbord, name='dashbord'),
    path('trips/', views.trips, name='trips'),
    path('add_booking/', views.add_booking, name='add_booking'),
    path('verify_booking/', views.verify_booking, name='verify_booking'),
    path('ride_completed/', views.ride_completed, name='ride_completed'),
    path('cancel_booking/', views.cancel_booking, name='cancel_booking'),

    # owner 
    path('owner_reg/', views.owner_reg, name='owner_reg'),
    path('owner_login/', views.owner_login, name='owner_login'),
    path('owner_logout/', views.owner_logout, name='owner_logout'),
    path('owner/', views.owner, name='owner'),
    path('edit_owner_profile/', views.edit_owner_profile, name='edit_owner_profile'),
    path('change_owner_password/', views.change_owner_password, name='change_owner_password'),
    path('add_trip/', views.add_trip, name='add_trip'),
    path('edit_trip/<int:id>/', views.edit_trip, name='edit_trip'),
    path('delete_trip/', views.delete_trip, name='delete_trip'),
    path('send_feedback_owner/', views.send_feedback_owner, name='send_feedback_owner'),
    path('send_feedback_rider/', views.send_feedback_rider, name="send_feedback_rider"),
    path('withdraw/', views.withdraw, name='withdraw'),

    # rider 
    path('rider_reg/', views.rider_reg, name='rider_reg'),
    path('rider_login/', views.rider_login, name='rider_login'),
    path('rider_logout/', views.rider_logout, name='rider_logout'),
    path('rider/', views.rider, name='rider'),
    path('edit_rider_profile/', views.edit_rider_profile, name='edit_rider_profile'),
    path('change_rider_password/', views.change_rider_password, name='change_rider_password'),
    
    path('review/', views.review, name="review"),
    path('about/', views.about, name='about'),
    path('support/', views.support, name='support'),
    path('support_form/', views.support_form, name='support_form'),
    path('map/', views.map, name='map'),

    # ajex fetch for filter trips in owner dashboard
    path('filter_trips/', views.filter_trips, name='filter_trips'),
    path('filter_bookings/', views.filter_bookings, name='filter_bookings'),
    path('top_up/', views.top_up, name='top_up'),
    path('topup_paid/', views.topup_paid, name='topup_paid')
]
