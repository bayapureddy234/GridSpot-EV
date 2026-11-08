\# GridSpot EV – EV Charging Station Finder



\## About the Project



GridSpot EV is a web-based application that helps electric vehicle users find nearby EV charging stations using location-based services.



\## Features



\- GPS-based nearby charging station search

\- Search stations by city and area

\- Urban and outskirts comparison

\- MySQL database integration

\- OpenStreetMap station discovery

\- Interactive maps

\- Charger availability information

\- Driving directions

\- Django Admin panel



\## Technologies Used



\- Python

\- Django

\- MySQL

\- HTML

\- CSS

\- JavaScript

\- MapLibre GL JS

\- OpenStreetMap

\- Nominatim

\- Overpass API

\- OSRM



\## Installation



\### 1. Clone the project



```bash

git clone YOUR\_GITHUB\_REPOSITORY\_URL

cd GridSpot-EV

```



\### 2. Create virtual environment



```bash

py -m venv venv

```



\### 3. Activate virtual environment



```bash

venv\\Scripts\\activate

```



\### 4. Install packages



```bash

py -m pip install -r requirements.txt

```



\### 5. Configure environment variables



Create a `.env` file with your own MySQL database details and Django secret key.



Never upload your `.env` file to GitHub.



\### 6. Run migrations



```bash

py manage.py migrate

```



\### 7. Start the server



```bash

py manage.py runserver

```



Open http://127.0.0.1:8000/ in your browser.



\## Project Purpose



This project demonstrates Python full-stack development, Django backend development, MySQL database integration, frontend development, and location-based services.



