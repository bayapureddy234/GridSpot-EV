
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from stations.models import City, Area, ChargingStation, Charger, ChargingSession


class Command(BaseCommand):
    help = "Load GridSpot EV sample data"

    def handle(self, *args, **kwargs):

        # 5 cities and 4 areas in each city
        city_data = {
            "Bengaluru": [
                ("Marathahalli", "Urban", 12.9592, 77.6974),
                ("Whitefield", "Urban", 12.9698, 77.7500),
                ("Electronic City", "Outskirts", 12.8399, 77.6770),
                ("Yelahanka", "Outskirts", 13.1007, 77.5963),
            ],
            "Hyderabad": [
                ("Gachibowli", "Urban", 17.4401, 78.3489),
                ("Madhapur", "Urban", 17.4483, 78.3915),
                ("Kukatpally", "Outskirts", 17.4849, 78.4138),
                ("Uppal", "Outskirts", 17.4017, 78.5590),
            ],
            "Chennai": [
                ("T Nagar", "Urban", 13.0418, 80.2341),
                ("Velachery", "Urban", 12.9815, 80.2180),
                ("Anna Nagar", "Outskirts", 13.0850, 80.2101),
                ("Tambaram", "Outskirts", 12.9249, 80.1000),
            ],
            "Mumbai": [
                ("Andheri", "Urban", 19.1197, 72.8464),
                ("Bandra", "Urban", 19.0596, 72.8295),
                ("Powai", "Outskirts", 19.1176, 72.9060),
                ("Thane", "Outskirts", 19.2183, 72.9781),
            ],
            "Delhi": [
                ("Connaught Place", "Urban", 28.6315, 77.2167),
                ("Dwarka", "Urban", 28.5921, 77.0460),
                ("Rohini", "Outskirts", 28.7495, 77.0565),
                ("Saket", "Outskirts", 28.5245, 77.2066),
            ],
        }

        states = {
            "Bengaluru": "Karnataka",
            "Hyderabad": "Telangana",
            "Chennai": "Tamil Nadu",
            "Mumbai": "Maharashtra",
            "Delhi": "Delhi",
        }

        session_number = 1

        for city_name, areas in city_data.items():

            city, _ = City.objects.get_or_create(
                city_name=city_name,
                defaults={
                    "state": states[city_name],
                    "country": "India",
                }
            )

            for area_name, area_type, latitude, longitude in areas:

                area, _ = Area.objects.get_or_create(
                    area_name=area_name,
                    city=city,
                    defaults={"area_type": area_type}
                )

                # Create 3 stations in every area
                for station_number in range(1, 4):

                    station_name = (
                        f"GridSpot {area_name} Station {station_number}"
                    )

                    station, _ = ChargingStation.objects.get_or_create(
                        station_name=station_name,
                        area=area,
                        defaults={
                            "address": f"{area_name}, {city_name}, India",
                            "latitude": Decimal(str(
                                round(latitude + (station_number * 0.001), 7)
                            )),
                            "longitude": Decimal(str(
                                round(longitude + (station_number * 0.001), 7)
                            )),
                            "operator_name": "GridSpot EV",
                            "contact_number": "9000000000",
                            "is_active": True,
                        }
                    )

                    # Create 2 chargers in every station
                    chargers = []

                    for charger_number in range(1, 3):

                        charger, _ = Charger.objects.get_or_create(
                            charger_name=f"Charger {charger_number}",
                            station=station,
                            defaults={
                                "charger_type": (
                                    "AC" if charger_number == 1 else "DC"
                                ),
                                "charging_speed": (
                                    Decimal("22.00")
                                    if charger_number == 1
                                    else Decimal("60.00")
                                ),
                                "connector_type": (
                                    "Type 2" if charger_number == 1
                                    else "CCS2"
                                ),
                                "price_per_unit": Decimal("18.00"),
                                "total_units": 1,
                                "available_units": (
                                    1 if charger_number == 1 else 0
                                ),
                                "is_active": True,
                            }
                        )

                        chargers.append(charger)

                    # Create 5 sessions per station
                    for i in range(1, 6):

                        charger = chargers[(i - 1) % 2]

                        start = timezone.now() - timedelta(
                            hours=i * 2
                        )

                        end = (
                            None if i == 5
                            else start + timedelta(minutes=45)
                        )

                        ChargingSession.objects.get_or_create(
                            vehicle_number=(
                                f"GS-{session_number:04d}"
                            ),
                            defaults={
                                "vehicle_type": [
                                    "Two Wheeler",
                                    "Four Wheeler",
                                    "Commercial",
                                ][(i - 1) % 3],
                                "start_time": start,
                                "end_time": end,
                                "energy_consumed": Decimal("20.00"),
                                "total_cost": Decimal("360.00"),
                                "charger": charger,
                            }
                        )

                        session_number += 1

        self.stdout.write(
            self.style.SUCCESS(
                "GridSpot EV sample data loaded successfully!"
            )
        )

        self.stdout.write("Cities: 5")
        self.stdout.write("Areas: 20")
        self.stdout.write("Stations: 60")
        self.stdout.write("Chargers: 120")
        self.stdout.write("Charging Sessions: 300")