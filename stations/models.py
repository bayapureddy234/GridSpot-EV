
from django.db import models


# --------------------------------------------------
# 1. CITY MODEL
# --------------------------------------------------

class City(models.Model):

    city_name = models.CharField(max_length=100)

    state = models.CharField(max_length=100)

    country = models.CharField(
        max_length=100,
        default="India"
    )

    def __str__(self):
        return self.city_name


# --------------------------------------------------
# 2. AREA MODEL
# --------------------------------------------------

class Area(models.Model):

    AREA_TYPES = [
        ('Urban', 'Urban'),
        ('Outskirts', 'Outskirts'),
    ]

    area_name = models.CharField(max_length=100)

    area_type = models.CharField(
        max_length=20,
        choices=AREA_TYPES
    )

    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name='areas'
    )

    def __str__(self):
        return self.area_name


# --------------------------------------------------
# 3. CHARGING STATION MODEL
# --------------------------------------------------

class ChargingStation(models.Model):

    station_name = models.CharField(max_length=150)

    address = models.TextField()

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7
    )

    operator_name = models.CharField(max_length=100)

    contact_number = models.CharField(max_length=15)

    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name='stations'
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.station_name


# --------------------------------------------------
# 4. CHARGER MODEL
# --------------------------------------------------

class Charger(models.Model):

    CHARGER_TYPES = [
        ('AC', 'AC Charger'),
        ('DC', 'DC Fast Charger'),
    ]

    charger_name = models.CharField(max_length=100)

    charger_type = models.CharField(
        max_length=20,
        choices=CHARGER_TYPES
    )

    charging_speed = models.DecimalField(
        max_digits=6,
        decimal_places=2
    )

    connector_type = models.CharField(max_length=50)

    price_per_unit = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    total_units = models.PositiveIntegerField(default=1)

    available_units = models.PositiveIntegerField(default=1)

    station = models.ForeignKey(
        ChargingStation,
        on_delete=models.CASCADE,
        related_name='chargers'
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.charger_name


# --------------------------------------------------
# 5. CHARGING SESSION MODEL
# --------------------------------------------------

class ChargingSession(models.Model):

    VEHICLE_TYPES = [
        ('Two Wheeler', 'Two Wheeler'),
        ('Four Wheeler', 'Four Wheeler'),
        ('Commercial', 'Commercial'),
    ]

    vehicle_number = models.CharField(max_length=20)

    vehicle_type = models.CharField(
        max_length=30,
        choices=VEHICLE_TYPES
    )

    start_time = models.DateTimeField()

    end_time = models.DateTimeField(
        null=True,
        blank=True
    )

    energy_consumed = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )

    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    charger = models.ForeignKey(
        Charger,
        on_delete=models.CASCADE,
        related_name='sessions'
    )

    def __str__(self):
        return self.vehicle_number
