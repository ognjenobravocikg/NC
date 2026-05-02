# Data Engineering Challenge

Project by Ognjen Obradović.

Challenge provided by Nordeus, you can download the analyze the challenge and download the dataset with the link: https://nordeus.com/nordeus-challenge/data-engineering/

The main goals of the project are:

- Parsing and cleaning raw `.jsonl` event data
- Storing structured data in a SQLite database
- Computing of the statistics (user stats, map stats)
- Exposing and providing API results via FastAPI

---

## Tech Stack

- Python 3.10+
- FastAPI
- SQLAlchemy
- SQLite
- Uvicorn
- Chart.js (frontend)

---

## Setup Instructions

### 1. Setting up

```
git clone https://github.com/ognjenobravocikg/NC.git
cd NC
```

After cloning the repo, in your IDE or File Manager you should be able to see this file structure

```
project/
│
├── app/
│   ├── api.py
│   ├── stats.py
│   ├── database.py
│   ├── models.py
│   ├── loader.py
│   ├── parser.py
│   └── static/
│       ├── index.html
│       ├── chart.html
│       └── profile.html
│
├── data/
│   ├── events.jsonl
│   └── maps.jsonl
│
├── main.py
├── requirements.txt
```

You should be able to download the project dependencies via the terminal and using the command

```
pip install -r requirements.txt
```

---

### 2. Load data into database

In the main project directory

```
python main.py
```

This will parse the data, clean the invalid rows and populate the SQLite database in the main project directory called 'nord_challenge.db'. For viewing the database you can use something like DB Browser and open the database.

---

### 3. Run API server

Also in the main project directory

```
uvicorn app.api:app --reload
```

In your browser go to the domain provided in the terminal. That will get you to the main landing page

---

## Usage

### Landing Page

```
http://127.0.0.1:8000/
```

Now when you are at the landing page, you can either navigate to the charts which contain multiple relevant charts for the bonuses of the challenge.

## API Endpoints

### Get Map Stats

```
GET /map-stats/{map_name}
```

Optional query params:

- `start_date` (YYYY-MM-DD)
- `end_date` (YYYY-MM-DD)

---

### Get User Stats

```
GET /user-stats
```

Optional filters:

- `countries`
- `oss`

---

## Data Processing

The parser performs:

- validation of all event types
- duplicate removal using business keys
- filtering malformed records

The loader:

- inserts cleaned data into SQL database
- handles repeated IDs (keeps earliest event)
- normalizes match events

---

## Features Implemented

- Efficient one-pass data processing
- SQL-based storage for fast querying
- REST API with filtering
- Match duration calculation from start/finish events
- Best player computation using win ratios
- Frontend visualization of match counts

---

## Bonus Features

- SQL database integration
- REST API implementation
- Data cleaning pipeline
- Interactive chart visualization

---

## Notes

- Database is SQLite (local file)
- Data must be loaded before running API
- Dates are handled in UTC

---

## Author

Ognjen Obradović e-mail: ognjenobradovickg@gmail.com
