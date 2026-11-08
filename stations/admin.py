from django.contrib import admin
from .models import (
    City,
    Area,
    ChargingStation,
    Charger,
    ChargingSession
)

admin.site.register(City)
admin.site.register(Area)
admin.site.register(ChargingStation)
admin.site.register(Charger)
admin.site.register(ChargingSession)