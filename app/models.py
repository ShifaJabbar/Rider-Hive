# © https://github.com/MrMKN
# Full Stacked By Mr MKN
from django.db import models

class Owner(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    license = models.CharField(max_length=20)
    address = models.TextField()
    phone = models.IntegerField(null=True, blank=True)
    password = models.CharField(max_length=25)
    car_name = models.CharField(max_length=200)
    car_number = models.CharField(max_length=20)
    cash = models.FloatField(default=0)

    def __str__(self):
        return self.name
    

class Rider(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    address = models.TextField()
    phone = models.IntegerField(null=True, blank=True)
    password = models.CharField(max_length=25)
    cash = models.FloatField(default=0)

    def __str__(self):
        return self.name

class SeatChoices(models.IntegerChoices):
    TWO_SEATER = 2, 'Two-seater'
    FOUR_SEATER = 4, 'Four-seater'
    SIX_SEATER = 6, 'Six-seater'
    EIGHT_SEATER = 8, 'Eight-seater'

class Trip(models.Model):
    map_image = models.ImageField(upload_to='maps/', default='map.png')

    origin_lat = models.FloatField()
    origin_lon = models.FloatField()
    origin = models.CharField(max_length=600)

    destination_lat = models.FloatField()
    destination_lon = models.FloatField()
    destination = models.CharField(max_length=600)

    distance = models.FloatField()
    amount = models.FloatField()

    owner = models.ForeignKey(Owner, on_delete=models.CASCADE)
    seats = models.IntegerField(choices=SeatChoices.choices, default=SeatChoices.FOUR_SEATER)
    start_time = models.TimeField()
    start_date = models.DateField()
    status = models.CharField(max_length=30, choices=[('P', 'Pending'), ('B', 'Booked'), ('V', 'Verified')], default='P')
    is_expired = models.BooleanField(default=False)
    is_booked = models.BooleanField(default=False)

    STATUS_COLORS = {
        'P': 'warning',
        'B': 'success',
        'V': 'primary',
    }

    def get_status_color(self):
        return self.STATUS_COLORS.get(self.status, 'secondary') 

    def __str__(self):
        return f"{self.origin} | {self.destination}: {self.owner.name}"


class Booking(models.Model):
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    is_done = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.rider.name} | {self.trip.owner.name}"
    


