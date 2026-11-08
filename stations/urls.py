
from django.urls import path
from . import views

urlpatterns = [

    # HOME PAGE
    path('', views.home, name='home'),

    # ADD NEW CITY
    path('add-city/', views.add_city, name='add_city'),

    # GET AREAS
    path(
        'get-areas/<int:city_id>/',
        views.get_areas,
        name='get_areas'
    ),

    # DETECT USER LOCATION
    path(
        'detect-location/',
        views.detect_location,
        name='detect_location'
    ),

    # SEARCH STATIONS
    path(
        'search-stations/',
        views.search_stations,
        name='search_stations'
    ),

    # MYSQL NEARBY STATIONS
    path(
        'nearby-stations/',
        views.nearby_stations,
        name='nearby_stations'
    ),

    # OPENSTREETMAP NEARBY STATIONS
    path(
        'nearby-osm-stations/',
        views.nearby_osm_stations,
        name='nearby_osm_stations'
    ),

]
