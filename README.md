# GridSpot EV

**EV Charging Station Finder & Intelligence Platform**

## About

GridSpot EV is a Django-based web application that helps electric vehicle users find nearby EV charging stations using GPS and location-based services.

It combines MySQL database integration with OpenStreetMap services to display charging stations, charger information, interactive maps, and driving directions.

## Features

- GPS-based nearby charging station search
- Search by city and locality
- Urban and outskirts comparison
- MySQL database integration
- OpenStreetMap station discovery
- Interactive maps with MapLibre GL JS
- Charger availability and occupancy information
- Driving directions using OSRM
- Django Admin for data management

## Technologies

- **Backend:** Python, Django
- **Database:** MySQL
- **Frontend:** HTML, CSS, JavaScript
- **Maps:** MapLibre GL JS, OpenStreetMap
- **APIs:** Nominatim, Overpass API, OSRM
- **Version Control:** Git, GitHub

## Project Structure

```text
GridSpot-EV/
├── config/
├── stations/
│   ├── management/
│   ├── migrations/
│   ├── static/
│   └── templates/
├── .env.example
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

## Run Locally

```bash
git clone https://github.com/bayapureddy234/GridSpot-EV.git
cd GridSpot-EV

py -m venv venv
venv\Scripts\activate

py -m pip install -r requirements.txt
py manage.py migrate
py manage.py runserver
```

Configure your MySQL database and `.env` file before running migrations.

## Future Enhancements

- User authentication
- Advanced station filtering
- Real-time charger availability
- Charging station analytics
- Station reviews and ratings

---

**GridSpot EV – Making EV charging discovery easier.**