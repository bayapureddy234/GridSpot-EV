import json
import math
import hashlib
import re
import urllib.parse
import urllib.request

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.cache import cache
from django.contrib import messages

from .models import City, Area, ChargingStation, Charger


# ==================================================
# HOME PAGE
# ==================================================

def home(request):
    cities = City.objects.all().order_by("city_name")
    return render(request, "stations/home.html", {"cities": cities})


# ==================================================
# ADD CITY
# ==================================================

def add_city(request):
    if request.method == "POST":
        city_name = request.POST.get("city_name", "").strip()
        state = request.POST.get("state", "").strip()
        country = request.POST.get("country", "India").strip()

        if not city_name or not state or not country:
            messages.error(request, "Please fill in all fields.")
            return render(request, "stations/add_city.html")

        exists = City.objects.filter(
            city_name__iexact=city_name,
            state__iexact=state,
            country__iexact=country
        ).exists()

        if exists:
            messages.warning(request, "This city already exists.")
            return render(request, "stations/add_city.html")

        City.objects.create(
            city_name=city_name,
            state=state,
            country=country
        )

        messages.success(request, f"{city_name} added successfully!")
        return redirect("home")

    return render(request, "stations/add_city.html")


# ==================================================
# GET AREAS
# ==================================================

@require_GET
def get_areas(request, city_id):
    areas = Area.objects.filter(
        city_id=city_id
    ).order_by("area_name")

    return JsonResponse({
        "success": True,
        "areas": [
            {
                "id": area.id,
                "area_name": area.area_name,
                "area_type": area.area_type
            }
            for area in areas
        ]
    })


# ==================================================
# LOCATION NORMALIZATION
# ==================================================

def normalize_location_name(name):
    if not name:
        return ""

    name = str(name).strip().lower()

    name = re.sub(
        r"\b(urban district|rural district|district)\b",
        "",
        name
    )

    name = re.sub(r"[^a-z0-9]", "", name)

    aliases = {
        "bengaluru": "bangalore",
        "bangalore": "bangalore",
        "bangaloreurban": "bangalore",
        "bangalorerural": "bangalore",
        "mysuru": "mysore",
        "mysore": "mysore",
        "mangaluru": "mangalore",
        "mangalore": "mangalore"
    }

    return aliases.get(name, name)


def city_name_matches(city_name, location_name):
    first = normalize_location_name(city_name)
    second = normalize_location_name(location_name)

    return bool(first and second and first == second)


def find_matching_city(detected_city, detected_state=""):
    if not detected_city:
        return None

    matching_cities = []

    for city in City.objects.all().order_by("id"):
        if city_name_matches(city.city_name, detected_city):
            matching_cities.append(city)

    if not matching_cities:
        return None

    if detected_state:
        normalized_state = normalize_location_name(detected_state)

        for city in matching_cities:
            if normalize_location_name(city.state) == normalized_state:
                return city

    return matching_cities[0]


# ==================================================
# MATCH LOCALITY WITH MYSQL AREA
# ==================================================

def find_matching_area(city, locality_names):
    if not city or not locality_names:
        return None

    areas = list(
        Area.objects.filter(city=city).order_by("id")
    )

    normalized_localities = []

    for locality in locality_names:
        normalized = normalize_location_name(locality)

        if normalized and normalized not in normalized_localities:
            normalized_localities.append(normalized)

    # Exact match first.
    for locality in normalized_localities:
        for area in areas:
            if normalize_location_name(area.area_name) == locality:
                return area

    # Careful partial match second.
    for locality in normalized_localities:
        for area in areas:
            area_name = normalize_location_name(area.area_name)

            if (
                len(area_name) >= 5
                and len(locality) >= 5
                and (
                    area_name in locality
                    or locality in area_name
                )
            ):
                return area

    return None


# ==================================================
# REVERSE GEOCODING
# ==================================================

def reverse_geocode(latitude, longitude):
    cache_key = "gridspot_reverse_" + hashlib.md5(
        f"{latitude:.5f}_{longitude:.5f}".encode()
    ).hexdigest()

    cached_data = cache.get(cache_key)

    if cached_data is not None:
        return cached_data

    url = (
        "https://nominatim.openstreetmap.org/reverse?"
        + urllib.parse.urlencode({
            "lat": latitude,
            "lon": longitude,
            "format": "jsonv2",
            "addressdetails": 1,
            "zoom": 18
        })
    )

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "GridSpotEV/1.0 (EV charging station finder)",
            "Accept-Language": "en"
        }
    )

    with urllib.request.urlopen(req, timeout=15) as response:
        location_data = json.loads(
            response.read().decode("utf-8")
        )

    cache.set(cache_key, location_data, 86400)
    return location_data


# ==================================================
# DETECT LOCATION
# ==================================================

@require_GET
def detect_location(request):
    latitude = request.GET.get("lat")
    longitude = request.GET.get("lon") or request.GET.get("lng")

    if not latitude or not longitude:
        return JsonResponse({
            "success": False,
            "error": "Latitude and longitude are required."
        }, status=400)

    try:
        latitude = float(latitude)
        longitude = float(longitude)

        if not (-90 <= latitude <= 90):
            raise ValueError

        if not (-180 <= longitude <= 180):
            raise ValueError

    except (ValueError, TypeError):
        return JsonResponse({
            "success": False,
            "error": "Invalid coordinates."
        }, status=400)

    try:
        location_data = reverse_geocode(latitude, longitude)
        address = location_data.get("address", {})

        # City candidates returned by OpenStreetMap.
        city_candidates = [
            address.get("city"),
            address.get("town"),
            address.get("municipality"),
            address.get("city_district"),
            address.get("county"),
            address.get("state_district")
        ]

        detected_city = next(
            (item for item in city_candidates if item),
            ""
        )

        detected_state = address.get("state", "")
        detected_country = address.get("country", "")

        # Locality candidates, in priority order.
        locality_names = [
            address.get("suburb"),
            address.get("neighbourhood"),
            address.get("quarter"),
            address.get("residential"),
            address.get("village"),
            address.get("hamlet"),
            address.get("city_block")
        ]

        locality_names = [
            str(item).strip()
            for item in locality_names
            if item and str(item).strip()
        ]

        detected_locality = (
            locality_names[0] if locality_names else ""
        )

        # Try each city candidate until a database city matches.
        matched_city = None

        for candidate in city_candidates:
            if candidate:
                matched_city = find_matching_city(
                    candidate,
                    detected_state
                )

                if matched_city:
                    detected_city = candidate
                    break

        matched_area = None

        if matched_city:
            matched_area = find_matching_area(
                matched_city,
                locality_names
            )

        return JsonResponse({
            "success": True,
            "latitude": latitude,
            "longitude": longitude,

            "city": detected_city,
            "state": detected_state,
            "country": detected_country,
            "locality": detected_locality,

            "display_name": location_data.get("display_name", ""),

            "city_id": matched_city.id if matched_city else None,
            "matched_city": (
                matched_city.city_name if matched_city else ""
            ),

            "area_id": matched_area.id if matched_area else None,
            "matched_area": (
                matched_area.area_name if matched_area else ""
            )
        })

    except Exception as error:
        print("GRIDSPOT LOCATION ERROR:", str(error))

        return JsonResponse({
            "success": False,
            "error": "Unable to detect city and locality."
        }, status=502)


# ==================================================
# CHARGER DETAILS
# ==================================================

def get_station_charger_details(station):
    chargers = Charger.objects.filter(
        station=station,
        is_active=True
    )

    charger_count = chargers.count()

    total_units = 0
    available_units = 0
    charger_details = []

    for charger in chargers:
        total_units += charger.total_units
        available_units += charger.available_units

        charger_details.append({
            "id": charger.id,
            "charger_name": charger.charger_name,
            "charger_type": charger.charger_type,
            "charging_speed": float(charger.charging_speed),
            "connector_type": charger.connector_type,
            "price_per_unit": float(charger.price_per_unit),
            "total_units": charger.total_units,
            "available_units": charger.available_units,
            "is_active": charger.is_active
        })

    occupied_units = max(total_units - available_units, 0)

    occupancy_percentage = (
        round((occupied_units / total_units) * 100, 2)
        if total_units > 0 else 0
    )

    return {
        "charger_count": charger_count,

        # These aliases are used by the homepage JavaScript.
        "total_chargers": total_units,
        "available_chargers": available_units,
        "busy_chargers": occupied_units,

        "total_units": total_units,
        "available_units": available_units,
        "occupied_units": occupied_units,
        "occupancy_percentage": occupancy_percentage,
        "chargers": charger_details
    }


# ==================================================
# STATION SERIALIZER
# ==================================================

def serialize_station(station):
    charger_data = get_station_charger_details(station)

    return {
        "id": station.id,
        "station_name": station.station_name,
        "name": station.station_name,
        "address": station.address,

        "latitude": float(station.latitude),
        "longitude": float(station.longitude),

        "operator_name": station.operator_name,
        "contact_number": station.contact_number,

        "area": station.area.area_name,
        "area_type": station.area.area_type,
        "city": station.area.city.city_name,

        "is_active": station.is_active,
        "station_status": (
            "Open" if station.is_active else "Closed"
        ),

        "source": "MySQL",
        "availability_unknown": False,

        "charger_count": charger_data["charger_count"],
        "total_chargers": charger_data["total_chargers"],
        "available_chargers": charger_data["available_chargers"],
        "busy_chargers": charger_data["busy_chargers"],

        "total_units": charger_data["total_units"],
        "available_units": charger_data["available_units"],
        "occupied_units": charger_data["occupied_units"],
        "occupancy_percentage": charger_data["occupancy_percentage"],

        "chargers": charger_data["chargers"]
    }


# ==================================================
# SEARCH STATIONS BY CITY AND AREA
# ==================================================

@require_GET
def search_stations(request):
    city_id = request.GET.get("city")
    area_id = request.GET.get("area")

    stations = ChargingStation.objects.filter(
        is_active=True
    ).select_related(
        "area",
        "area__city"
    ).prefetch_related("chargers")

    selected_city = None
    selected_area = None

    if city_id:
        selected_city = City.objects.filter(id=city_id).first()
        stations = stations.filter(area__city_id=city_id)

    if area_id:
        selected_area = Area.objects.filter(id=area_id).first()
        stations = stations.filter(area_id=area_id)

    station_data = [
        serialize_station(station)
        for station in stations.order_by("station_name")
    ]

    return JsonResponse({
        "success": True,
        "count": len(station_data),
        "city": selected_city.city_name if selected_city else "",
        "area": selected_area.area_name if selected_area else "",
        "stations": station_data
    })


# ==================================================
# DISTANCE CALCULATION
# ==================================================

def calculate_distance(lat1, lon1, lat2, lon2):
    earth_radius = 6371

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    difference_lat = lat2 - lat1
    difference_lon = lon2 - lon1

    a = (
        math.sin(difference_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(difference_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius * c


# ==================================================
# NEARBY MYSQL STATIONS
# ==================================================

@require_GET
def nearby_stations(request):
    latitude = request.GET.get("lat")
    longitude = request.GET.get("lon") or request.GET.get("lng")
    radius = request.GET.get("radius", 10)

    if not latitude or not longitude:
        return JsonResponse({
            "success": False,
            "error": "Latitude and longitude are required."
        }, status=400)

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        radius = float(radius)

        if not (-90 <= latitude <= 90):
            raise ValueError

        if not (-180 <= longitude <= 180):
            raise ValueError

        if not (0 < radius <= 500):
            raise ValueError

    except (ValueError, TypeError):
        return JsonResponse({
            "success": False,
            "error": "Invalid location or radius."
        }, status=400)

    station_queryset = ChargingStation.objects.filter(
        is_active=True
    ).select_related(
        "area",
        "area__city"
    ).prefetch_related("chargers")

    nearby_results = []

    for station in station_queryset:
        distance = calculate_distance(
            latitude,
            longitude,
            station.latitude,
            station.longitude
        )

        if distance <= radius:
            station_data = serialize_station(station)
            station_data["distance"] = round(distance, 2)
            nearby_results.append(station_data)

    nearby_results.sort(key=lambda item: item["distance"])

    return JsonResponse({
        "success": True,
        "count": len(nearby_results),
        "radius": radius,
        "stations": nearby_results
    })


# ==================================================
# OPENSTREETMAP NEARBY STATIONS
# ==================================================

@require_GET
def nearby_osm_stations(request):
    latitude = request.GET.get("lat")
    longitude = request.GET.get("lon") or request.GET.get("lng")
    radius = request.GET.get("radius", 10)

    if not latitude or not longitude:
        return JsonResponse({
            "success": False,
            "error": "Latitude and longitude are required."
        }, status=400)

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        radius = float(radius)

        if not (-90 <= latitude <= 90):
            raise ValueError

        if not (-180 <= longitude <= 180):
            raise ValueError

        if not (0 < radius <= 500):
            raise ValueError

    except (ValueError, TypeError):
        return JsonResponse({
            "success": False,
            "error": "Invalid location or radius."
        }, status=400)

    radius_meters = int(radius * 1000)

    cache_text = (
        f"{latitude:.4f}_{longitude:.4f}_{radius_meters}"
    )

    cache_key = "gridspot_osm_" + hashlib.md5(
        cache_text.encode()
    ).hexdigest()

    cached_data = cache.get(cache_key)

    if cached_data is not None:
        return JsonResponse(cached_data)

    overpass_query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="charging_station"]
      (around:{radius_meters},{latitude},{longitude});

      way["amenity"="charging_station"]
      (around:{radius_meters},{latitude},{longitude});

      relation["amenity"="charging_station"]
      (around:{radius_meters},{latitude},{longitude});
    );
    out center tags;
    """

    overpass_servers = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]

    osm_stations = []
    last_error = None

    for server in overpass_servers:
        try:
            encoded_query = urllib.parse.urlencode({
                "data": overpass_query
            }).encode("utf-8")

            req = urllib.request.Request(
                server,
                data=encoded_query,
                headers={
                    "User-Agent": "GridSpotEV/1.0",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )

            with urllib.request.urlopen(req, timeout=35) as response:
                osm_data = json.loads(
                    response.read().decode("utf-8")
                )

            for element in osm_data.get("elements", []):
                tags = element.get("tags", {})

                element_lat = element.get("lat")
                element_lon = element.get("lon")

                if element_lat is None or element_lon is None:
                    center = element.get("center", {})
                    element_lat = center.get("lat")
                    element_lon = center.get("lon")

                if element_lat is None or element_lon is None:
                    continue

                name = (
                    tags.get("name")
                    or tags.get("operator")
                    or "EV Charging Station"
                )

                distance = calculate_distance(
                    latitude,
                    longitude,
                    element_lat,
                    element_lon
                )

                if distance > radius:
                    continue

                osm_stations.append({
                    "id": f"osm_{element.get('type')}_{element.get('id')}",
                    "osm_id": element.get("id"),
                    "name": name,
                    "station_name": name,

                    "latitude": float(element_lat),
                    "longitude": float(element_lon),

                    "address": ", ".join(filter(None, [
                        tags.get("addr:street"),
                        tags.get("addr:suburb"),
                        tags.get("addr:city")
                    ])),

                    "operator_name": tags.get(
                        "operator", "Not specified"
                    ),

                    "charging_type": tags.get(
                        "socket:type2", "Not specified"
                    ),

                    "capacity": tags.get(
                        "capacity", "Not specified"
                    ),

                    "source": "OpenStreetMap",
                    "distance": round(distance, 2),

                    "is_live_availability": False,
                    "availability_unknown": True,

                    "available_chargers": None,
                    "total_chargers": None,
                    "busy_chargers": None,

                    "is_active": None,
                    "station_status": "Unknown"
                })

            break

        except Exception as error:
            last_error = str(error)

    else:
        return JsonResponse({
            "success": False,
            "error": "OpenStreetMap search is temporarily unavailable.",
            "details": last_error,
            "stations": []
        }, status=503)

    osm_stations.sort(key=lambda item: item["distance"])

    result = {
        "success": True,
        "source": "OpenStreetMap",
        "count": len(osm_stations),
        "radius": radius,
        "stations": osm_stations
    }

    cache.set(cache_key, result, 300)
    return JsonResponse(result)