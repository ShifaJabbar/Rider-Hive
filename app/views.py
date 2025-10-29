# © https://github.com/MrMKN
# Full Stacked By Mr MKN

from django.views.decorators.csrf import csrf_exempt 
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.utils.timezone import now
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
from .models import *
import base64, logging, qrcode, os, re

logging.getLogger(__name__).setLevel(logging.DEBUG)

# main views content
def dashbord(request):
    trips = Trip.objects.all()
    for trip in trips:
        if trip.start_date < now().date():
            trip.is_expired = True
            trip.save()
    
    trips = Trip.objects.filter(is_booked=False, is_expired=False).order_by('-id')[:8]
    context = dict(trips=trips)
    return render(request, 'dashbord.html', context)

def review(request):
    return render(request, 'review.html')

def trips(request):
    if 'rider' not in request.session:
        messages.warning(request, 'YOU NEED LOGIN')
        return redirect('rider_login')
    
    email = request.session['rider']
    rider = Rider.objects.get(email=email)
    
    if request.method == 'POST':
        origin = request.POST.get('origin')
        destination = request.POST.get('destination')
        date = request.POST.get('date')

        # Convert the input date string to a datetime.date object
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()

        # Calculate the range: 1 day before and 1 day after
        date_start = selected_date - timedelta(days=1)
        date_end = selected_date + timedelta(days=1)

        # Query the database
        result = Trip.objects.filter(
            Q(origin__icontains=origin) &
            Q(destination__icontains=destination) &
            Q(start_date__range=(date_start, date_end)) & 
            Q(is_expired=False) &
            Q(is_booked=False)
        )

        if result.exists():
            return render(request, 'trip_results.html', {'trips': result.order_by('-id')})
        else:
            messages.warning(request, 'No trips found matching your criteria. Check mannually to find your trip bellow')
            return render(request, 'trip_results.html', {'trips': Trip.objects.filter(is_booked=False, is_expired=False).order_by('-id')})
        
    return render(request, 'trip_results.html', {'trips': Trip.objects.filter(is_booked=False, is_expired=False).order_by('-id')})

def add_booking(request):
    if 'rider' not in request.session:
        messages.warning(request, 'YOU NEED LOGIN')
        return redirect('rider_login')
    
    if not request.method == 'POST': return

    email = request.session['rider']
    rider = Rider.objects.get(email=email)
    
    try:
        trip = Trip.objects.get(id=int(request.POST['trip']))
    except:
        messages.error(request, '! Trip Not Exist')
        return redirect('trips')
    
    if rider.cash < trip.amount:
        messages.warning(request, '! Insufficent balance. top up to book the trip')
        return redirect('trips')
    
    trip.is_booked = True
    trip.status = 'B'
    trip.save()

    data = Booking(rider=rider, trip=trip)
    data.save()

    try:
        subject = f'Ride Booked By:({email})'
        body = \
            f'Booked By: {email}\n'\
            f'Date: {trip.start_date} | {trip.start_time}\n'\
            f'Rider Ph: {rider.phone}\n'\
            f'Trip: \n\n'\
            f'from: {trip.origin}\n'\
            f'To: {trip.destination}\n\n'\
            'Verify to approve the ride in website. Thakyou'
        
        send_mail(subject, body, settings.EMAIL_HOST_USER, [trip.owner.email], fail_silently=False)
    except Exception as e:
        print(e) 
    
    messages.success(request, 'Ride Booked Successfull')
    return redirect('trips')

def verify_booking(request):
    if not 'owner' in request.session:
        messages.warning(request,'YOU NEED LOGIN')
        return redirect('owner_login')
    if not request.method == 'POST': return
    
    email = request.session['owner']
    owner = Owner.objects.get(email=email)
    try:
        trip = Trip.objects.get(id=int(request.POST['trip']))
        booking = Booking.objects.get(trip=trip)
        rider = booking.rider
    except:
        messages.error(request, '! Trip Not Exist')
        return redirect('owner')
    
    rider.cash = rider.cash - trip.amount
    rider.save()
    trip.status = 'V'
    trip.save()

    booking.is_verified = True
    booking.save()

    try:
        subject = f'Your Ride Verified'
        body = \
            f'Car Owner Email: {email}\n'\
            f'Owner Ph: {owner.phone}\n'\
            f'Car Number: {owner.car_number}\n'\
            f'Car Name: {owner.car_name}\n'\
            f'Available Seats: {trip.seats}\n'\
            f'Date: {trip.start_date} | {trip.start_time}\n'\
            f'Trip: \n\n'\
            f'from: {trip.origin}\n'\
            f'To: {trip.destination}\n\n'\
            'Contact Owner To Get The ride. Thakyou'
        
        send_mail(subject, body, settings.EMAIL_HOST_USER, [rider.email], fail_silently=False)
    except Exception as e:
        print(e) 
    
    messages.success(request, 'Ride Verified Successfull')
    return redirect('owner')

def cancel_booking(request):
    if 'rider' not in request.session:
        messages.warning(request, 'YOU NEED LOGIN')
        return redirect('rider_login')
    
    if not request.method == 'POST': return

    email = request.session['rider']
    rider = Rider.objects.get(email=email)
    
    try:
        booking = Booking.objects.get(id=int(request.POST['booking']))
    except:
        messages.error(request, '! Trip Not Exist')
        return redirect('rider')
    
    booking.trip.is_booked = False
    booking.trip.status = 'P'
    booking.trip.save()

    
    try:
        subject = f'Booking Cancelled: ({email})'
        body = \
            f'Booked By: {email}\n'\
            f'Date: {booking.trip.start_date} | {booking.trip.start_time}\n'\
            f'Rider Ph: {rider.phone}\n'\
            f'Trip: \n\n'\
            f'from: {booking.trip.origin}\n'\
            f'To: {booking.trip.destination}\n\n'
        
        send_mail(subject, body, settings.EMAIL_HOST_USER, [booking.trip.owner.email], fail_silently=False)
    except Exception as e:
        print(e) 
    booking.delete()
    
    messages.success(request, 'Ride Cancelled Successfully')
    return redirect('rider')

def ride_completed(request):
    if 'rider' not in request.session:
        messages.warning(request, 'YOU NEED LOGIN')
        return redirect('rider_login')
    
    if not request.method == 'POST': return

    email = request.session['rider']
    rider = Rider.objects.get(email=email)
    try:     
        trip = Trip.objects.get(id=int(request.POST['trip']))
        booking = Booking.objects.get(trip=trip)
        owner = trip.owner
    except Exception as e:
        messages.error(request, '! Trip Not Exist')
        return redirect('rider')
    
    owner.cash += trip.amount % 90
    owner.save()
    rider.save()
    booking.is_done = True
    booking.save()
    
    messages.success(request, 'Ride Completed Successfully')
    return redirect('rider')

def about(request):
    context = {}
    return render(request, 'about.html', context)

def support(request):
    context = {}
    return render(request, 'support.html', context)

def owner(request):
    if not 'owner' in request.session:
        messages.warning(request,'YOU NEED LOGIN')
        return redirect('owner_login')
    
    email = request.session['owner']
    owner = Owner.objects.get(email=email)

    trips = Trip.objects.filter(owner=owner).order_by('-id')
    bookings = Booking.objects.filter(trip__owner=owner).order_by('-id')
    owner.cash = f"{owner.cash:2f}"
    context = {
        'owner': owner,
        'trips': trips,
        'bookings': bookings     
    }
    return render(request, 'owner/owner.html', context)
    

def rider(request):
    if not 'rider' in request.session:
        messages.warning(request,'YOU NEED LOGIN')
        return redirect('rider_login')
    
    email = request.session['rider']
    rider = Rider.objects.get(email=email)
    bookings = Booking.objects.filter(rider=rider).order_by('-id')
    
    context = {
        'rider': rider,
        'bookings': bookings    
    }
    return render(request, 'rider/rider.html', context)


def map(request):
    return render(request, 'map.html') 


# Owner Auth Section
def owner_reg(request):
    if request.method =='POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        license = request.POST.get('license')
        car_name = request.POST.get('car_name')
        car_number = request.POST.get('car_number')
        address = request.POST.get('address')
        password = request.POST.get('password')
        owner = Rider.objects.filter(email=email).exists()
        if owner:
            messages.warning(request,'EMIAL ALREADY EXISTS')
            return redirect('owner_reg')
        else:
            data = Owner(name=name, email=email, password=password, phone=phone, license=license, car_name=car_name, car_number=car_number, address=address)
            data.save()
            messages.success(request,f'login to enter your account')
            return redirect('owner_login')    
    return render(request, 'owner/owner_reg.html', {})

def owner_login(request):
    if 'owner' in request.session:
        return redirect('owner')  
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        owner = Owner.objects.filter(email=email).exists()
        if not owner :
            messages.warning(request,'INVALID EMIAL ADDRESS')
            return redirect('owner_login')
        elif password != (Owner.objects.get(email=email)).password:
            messages.warning(request,'INCORRECT PASSWORD')
            return redirect('owner_login')
        else:
            owner = Owner.objects.get(email=email)
            request.session['owner'] = owner.email
            return redirect('owner')  
    return render(request, "owner/owner_login.html")


def edit_owner_profile(request):
    if not 'owner' in request.session:
        messages.warning(request, 'YOU NEED TO LOGIN')
        return redirect('owner_login')
    if not request.method == 'POST': return redirect('owner')

    try:
        email = request.POST.get('email')
        if (email != request.session['owner']) and (Owner.objects.filter(email=email).exists()):
            messages.warning(request, f'! The Email "{email}" already exist')
            return redirect('owner')
        user = Owner.objects.get(email=request.session['owner']) 
        user.name = request.POST.get('name')
        user.phone = request.POST.get('phone')
        user.license = request.POST.get('license')
        user.car_name = request.POST.get('car_name')
        user.car_number = request.POST.get('car_number')
        user.address = request.POST.get('address')
        user.email = email
        request.session['owner'] = email
        user.save()
        messages.success(request, 'Update Successfull ✔')
        return redirect('owner')
    except Exception as e:
        logging.exception(e)
        messages.error(request, '! Error. Account Not Exist')
        return redirect('owner')

def change_owner_password(request):
    if not 'owner' in request.session:
        messages.warning(request, 'YOU NEED TO LOGIN')
        return redirect('owner_login')
    if not request.method == 'POST': return redirect('owner')

    try:
        user = Owner.objects.get(email=request.session['owner']) 
        old = request.POST.get('old')
        new1 = request.POST.get('new1')
        new2 = request.POST.get('new2')
        if old != user.password:
            messages.warning(request, f'! Old Password Is Wrong')
            return redirect('owner')
        elif new1 != new2:
            messages.warning(request, f'! New password-1 not equal to password-2')
            return redirect('owner')
        elif new1 == old:
            messages.warning(request, f'! Old password and new password are same')
            return redirect('owner')
        
        user.password = new1
        user.save()
        messages.success(request, 'Password Changed Successfully ✔')
        return redirect('owner')
    except Exception as e:
        logging.exception(e)
        messages.error(request, '! Error. Account Not Exist')
        return redirect('owner')
    
def owner_logout(request):
    try:
        del request.session['owner']
    except:
        return redirect('owner_login')
    return redirect('owner_login')
    

# rider authentication
def rider_reg(request):
    if request.method =='POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        password = request.POST.get('password')     
        rider = Rider.objects.filter(email=email).exists()
        if rider:
            messages.warning(request,'EMIAL ALREADY EXISTS')
            return redirect('rider_reg')
        else:
            data = Rider(name=name, email=email, password=password, phone=phone, address=address)
            data.save()
            messages.success(request,f'login to enter your account')
            return redirect('rider_login')       
    return render(request, 'rider/rider_reg.html', {})

def rider_login(request):
    if 'rider' in request.session:
        return redirect('rider') 
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        rider = Rider.objects.filter(email=email).exists()
        if not rider :
            messages.warning(request,'INVALID EMIAL ADDRESS')
            return redirect('rider_login')
        elif password != (Rider.objects.get(email=email)).password:
            messages.warning(request,'INCORRECT PASSWORD')
            return redirect('rider_login')
        else:
            rider = Rider.objects.get(email=email)
            request.session['rider'] = rider.email
            return redirect('rider') 
    return render(request, "rider/rider_login.html")

def edit_rider_profile(request):
    if not 'rider' in request.session:
        messages.warning(request, 'YOU NEED TO LOGIN')
        return redirect('rider_login')
    if not request.method == 'POST': return redirect('rider')

    try:
        email = request.POST.get('email')
        if (email != request.session['rider']) and (Rider.objects.filter(email=email).exists()):
            messages.warning(request, f'! The Email "{email}" already exist')
            return redirect('rider')
        user = Rider.objects.get(email=request.session['rider']) 
        user.name = request.POST.get('name')
        user.phone = request.POST.get('phone')
        user.email = email
        user.address = request.POST.get('address')
        request.session['rider'] = email
        user.save()
        messages.success(request, 'Update Successfully ✔')
        return redirect('rider')
    except Exception as e:
        logging.exception(e)
        messages.error(request, '! Error. Account Not Exist')
        return redirect('rider')

def change_rider_password(request):
    if not 'rider' in request.session:
        messages.warning(request, 'YOU NEED TO LOGIN')
        return redirect('rider_login')
    if not request.method == 'POST': return redirect('rider')

    try:
        user = Rider.objects.get(email=request.session['rider']) 
        old = request.POST.get('old')
        new1 = request.POST.get('new1')
        new2 = request.POST.get('new2')
        if old != user.password:
            messages.warning(request, f'! Old Password Is Wrong')
            return redirect('rider')
        elif new1 != new2:
            messages.warning(request, f'! New password-1 not equal to password-2')
            return redirect('rider')
        elif new1 == old:
            messages.warning(request, f'! Old password and new password are same')
            return redirect('rider')
        
        user.password = new1
        user.save()
        messages.success(request, 'Password Changed Successfully ✔')
        return redirect('rider')
    except Exception as e:
        logging.exception(e)
        messages.error(request, '! Error. Account Not Exist')
        return redirect('rider')

def rider_logout(request):
    try:
        del request.session['rider']
    except:
        return redirect('rider_login')
    return redirect('rider_login')   
    

#add trip
def add_trip(request):
    if not 'owner' in request.session:
        messages.warning(request,'YOU NEED LOGIN')
        return redirect('owner_login')
    
    email = request.session['owner']
    owner = Owner.objects.get(email=email)

    if request.method == 'POST':
        data = request.POST    
        distance = data.get('distance')
        amount = float(distance) * 6
        # Save to the database
        map_image_file = request.FILES.get('map_image_file')

        trip = Trip(
            owner=owner,
            origin_lat=data.get('origin_lat'),
            origin_lon=data.get('origin_lon'),
            origin=data.get('origin_name'),
            destination_lat=data.get('destination_lat'),
            destination_lon=data.get('destination_lon'),
            destination=data.get('destination_name'),
            seats=data.get('seats_count'),
            start_time = data.get('start_time'),
            start_date = data.get('start_date'),
            distance=distance,
            amount=f'{amount:.2f}',
            map_image=map_image_file
        )
        trip.save()
        message = 'added successful '
        messages.success(request, message)
        return JsonResponse({'redirect': '/owner/', 'message': message}, status=200)
    
    return render(request, 'owner/add_trip.html')

#add trip
def edit_trip(request, id):
    if not 'owner' in request.session:
        messages.warning(request,'YOU NEED LOGIN')
        return redirect('owner_login')
    
    email = request.session['owner']
    owner = Owner.objects.get(email=email)
    try:
        trip = Trip.objects.get(owner=owner, id=id)
    except Exception as e:
        print(e)
        messages.warning(request,'Error!')
        return redirect('owner') 
    
    if request.method == 'POST':
        data = request.POST
        # Edit the data
        trip.origin_lat = float(data.get('origin_lat'))
        trip.origin_lon = float(data.get('origin_lon'))
        trip.origin = data.get('origin_name')
        trip.destination_lat = float(data.get('destination_lat'))
        trip.destination_lon = float(data.get('destination_lon'))
        trip.destination = data.get('destination_name')
        trip.distance = float(data.get('distance'))
        trip.seats = data.get('seats_count')
        trip.start_time = data.get('start_time')
        trip.start_date = data.get('start_date')
        trip.save()
        messages.success(request, 'Edit successful')
        return redirect('owner')

    context = dict(owner=owner, trip=trip)
    return render(request, 'owner/edit_trip.html', context)

def delete_trip(request):
    if not 'owner' in request.session:
        messages.warning(request,'YOU NEED LOGIN')
        return redirect('owner_login')
    
    if request.method == 'POST': 
        email = request.session['owner']
        owner = Owner.objects.get(email=email)
        id = int(request.POST['trip'])
        try:
            trip = Trip.objects.get(owner=owner, id=id)
            trip.delete()
            messages.success(request, 'Trip Successfully Deleteted ✔')
            return redirect('owner') 
        except Exception as e:
            print(e)
            messages.warning(request, 'Error!')
            return redirect('owner') 


def send_feedback_owner(request):
    if not 'owner' in request.session:
        messages.warning(request,'YOU NEED LOGIN')
        return redirect('owner_login')
    
    if request.method == 'POST':
        try:
            subject = f'FeedBack Of Rider Hive From [{request.session['owner']}]'
            body = request.POST.get('message')
            send_mail(subject, body, settings.EMAIL_HOST_USER, settings.OWNER_EMAIL, fail_silently=False)
            print("Email sent successfully!")
            messages.success(request, 'Email sent successfully ✔')
            return redirect('owner') 
        except Exception as e:
            print(f"Failed to send email: {e}")
            messages.error(request, f'Failed to send email: {e}')
            return redirect('owner') 
        
def send_feedback_rider(request):
    if not 'rider' in request.session:
        messages.warning(request,'YOU NEED LOGIN')
        return redirect('rider_login')
    
    if request.method == 'POST':
        try:
            subject = f'FeedBack Of Rider Hive From [{request.session['rider']}]'
            body = request.POST.get('message')
            send_mail(subject, body, settings.EMAIL_HOST_USER, settings.OWNER_EMAIL, fail_silently=False)
            print("Email sent successfully!")
            messages.success(request, 'Email sent successfully ✔')
            return redirect('rider') 
        except Exception as e:
            print(f"Failed to send email: {e}")
            messages.error(request, f'Failed to send email: {e}')
            return redirect('rider') 
        
def support_form(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        try:
            subject = f'RH: {name} ({email})'
            body = request.POST.get('message')
            send_mail(subject, body, settings.EMAIL_HOST_USER, settings.OWNER_EMAIL, fail_silently=False)
            print("Email sent successfully!")
            messages.success(request, 'Email sent successfully ✔')
            return redirect('support') 
        except Exception as e:
            print(f"Failed to send email: {e}")
            messages.error(request, f'Failed to send email: {e}')
            return redirect('support') 
    


# ajex fetch for filter trips in owner dashboard
def filter_trips(request):
    if not 'owner' in request.session:
        messages.warning(request,'YOU NEED LOGIN')
        return redirect('owner_login')
    
    email = request.session['owner']
    owner = Owner.objects.get(email=email)
    selected_status = request.GET.get('status', 'all')
    if selected_status == 'all':
        trips = Trip.objects.filter(owner=owner).order_by('-id')
    else:
        trips = Trip.objects.filter(owner=owner, status=selected_status).order_by('-id')

    trips_data = [
        {
            'id': trip.id,
            'origin': trip.origin,
            'destination': trip.destination,
            'start_date': str(trip.start_date),  
            'start_time': str(trip.start_time),  
            'distance': trip.distance,
            'amount': trip.amount,
            'is_expired': str(trip.is_expired),  
            'is_booked': trip.is_booked,
            'status': trip.get_status_display(), 
            'status_color': trip.get_status_color(),  
        }
        for trip in trips
    ]
    return JsonResponse({'trips': trips_data})

def filter_bookings(request):
    if not 'rider' in request.session:
        messages.warning(request,'YOU NEED LOGIN')
        return redirect('rider_login')
    
    email = request.session['rider']
    rider = Rider.objects.get(email=email)
    selected_status = request.GET.get('status', 'all')
    if selected_status == 'all':
        trips = Booking.objects.filter(rider=rider).order_by('-id')
    elif selected_status == 'F':
        trips = Booking.objects.filter(rider=rider, is_done=True).order_by('-id')
    elif selected_status == 'V':
        trips = Booking.objects.filter(rider=rider, is_verified=True).order_by('-id')

    trips_data = [
        {
            'id': trip.id,
            'origin': trip.trip.origin,
            'destination': trip.trip.destination,
            'start_date': str(trip.trip.start_date),  
            'start_time': str(trip.trip.start_time),  
            'distance': trip.trip.distance,
            'amount': trip.trip.amount,
            'owner_number': trip.trip.owner.phone,
            'is_expired': str(trip.trip.is_expired),  
            'is_booked': trip.trip.is_booked,
            'status': trip.trip.get_status_display(), 
            'status_color': trip.trip.get_status_color(), 
            'is_done': trip.is_done,
        }
        for trip in trips
    ]

    return JsonResponse({'trips': trips_data})


def top_up(request):
    if not 'rider' in request.session:
        messages.warning(request,'YOU NEED LOGIN')
        return redirect('rider_login')
    
    email = request.session['rider']
    rider = Rider.objects.get(email=email)
    if request.method == 'POST':
        amount = request.POST.get('amount')
        url = f"upi://pay?pa={settings.UPI_ID}&pn={email}&am={amount}&cu=INR&tn={email}"

        folder_path = f"media/payments_qrs/{email}/"
        os.makedirs(folder_path, exist_ok=True)
        timestamp = now().strftime("%Y%m%d_%H%M%S")
        sanitized_email = re.sub(r'[^\w\.\-]', '_', email)  
        qr_file_name = f"{folder_path}{timestamp}-[{amount}₹]-qrfood.png"
        
        qr = qrcode.make(str(url))
        qr.save(qr_file_name)

        qr_url = f"/{qr_file_name}"  
        return JsonResponse({'qr_url': qr_url, 'url': url, 'amount': amount}, status=200)
    
def topup_paid(request):
    if not 'rider' in request.session:
        messages.warning(request,'YOU NEED LOGIN')
        return redirect('rider_login')
    
    email = request.session['rider']
    rider = Rider.objects.get(email=email)
    if request.method == 'POST':
        amount = request.POST.get('amount')
        rider.cash += float(amount)
        rider.save()

        messages.success(request, f'Amount {amount}₹ Is Credited to your rider account')
        return redirect('rider') 
    
def withdraw(request):
    if not 'owner' in request.session:
        messages.warning(request,'YOU NEED LOGIN')
        return redirect('owner_login')
    
    email = request.session['owner']
    owner = Owner.objects.get(email=email)
    if request.method == 'POST':
        amount = float(request.POST.get('amount'))

        if amount > owner.cash:
            messages.warning(request, f'! Insufficent Balance')
            return redirect('owner')  

        owner.cash -= amount
        owner.save()

        messages.success(request, f'Amount {amount}₹ Withdraw Request Is Created Admin Will Verify And Transfer To You Soon...')
        return redirect('owner') 