# SIH26162_
# AI-Based Detection and Classification of Industrial Fires and Persistent Thermal Sources

## Smart India Hackathon 2026

### Problem Statement

Industrial facilities such as oil refineries, petrochemical complexes, thermal power plants, steel industries, mining areas and LNG terminals can produce thermal signatures that can be detected from satellite data.

However, satellite thermal anomaly systems may detect many different types of heat sources, including industrial fires, agricultural burning, forest fires and other temporary thermal sources.

The objective of this project is to develop an AI-enabled geospatial system that can identify, classify and monitor industrial fires and persistent thermal sources by combining satellite thermal data, land-cover information, industrial infrastructure data and historical hotspot behaviour.

---

## Project Objective

Our system aims to:

- Detect thermal hotspots using NASA FIRMS data.
- Identify the land-cover type around each hotspot.
- Check for nearby industrial infrastructure using OpenStreetMap.
- Analyze whether a hotspot is persistent or temporary.
- Classify thermal events into Industrial, Agricultural and Natural categories.
- Calculate a priority level for detected events.
- Generate Critical, Warning and Normal alerts.
- Display all results on an interactive GIS dashboard.

---

## Proposed Solution

The system follows a multi-source geospatial and AI-based approach.

### Processing Pipeline

NASA FIRMS Thermal Data
        ↓
Data Preprocessing
        ↓
ESA WorldCover Land Cover
        ↓
OpenStreetMap Industrial Context
        ↓
Historical Persistence Analysis
        ↓
Feature Engineering
        ↓
AI/ML Classification
        ↓
Industrial / Agricultural / Natural
        ↓
Priority Assessment
        ↓
Alert Generation
        ↓
Interactive GIS Dashboard

---

## Data Sources

### 1. NASA FIRMS

NASA FIRMS (Fire Information for Resource Management System) provides satellite-based thermal anomaly and fire detections.

It provides information such as:

- Latitude
- Longitude
- Brightness temperature
- Fire Radiative Power (FRP)
- Confidence
- Acquisition date and time

We use FIRMS to identify locations where thermal anomalies are detected.

### 2. ESA WorldCover

ESA WorldCover provides global land-cover information derived from satellite observations.

It helps identify whether a hotspot is located in:

- Cropland
- Tree cover
- Built-up area
- Grassland
- Shrubland
- Bare or sparse vegetation
- Other land-cover classes

### 3. OpenStreetMap

OpenStreetMap (OSM) provides geographic information about infrastructure and facilities.

We use OSM to identify nearby:

- Industrial areas
- Factories
- Power-related infrastructure
- Plants
- Other industrial features

### 4. Historical Hotspot Data

Previous thermal detections are analyzed to determine whether a hotspot repeatedly occurs in approximately the same location.

This helps distinguish persistent thermal sources from temporary events.

---

## AI/ML Approach

The project uses a **Random Forest Classifier** for thermal-source classification.

The model uses geographic and thermal features such as:

- Brightness
- FRP
- Confidence
- Land-cover type
- Number of detections
- Active days
- Persistence
- Nearby OSM features
- Distance to nearby industrial features

The current prototype classifies events into:

- **Industrial**
- **Agricultural**
- **Natural**

The model output also includes a prediction probability that is used as a confidence indicator.

> Note: The current prototype uses a small weakly labelled dataset for demonstration. The prediction probability should not be interpreted as formal real-world accuracy. A larger independently verified ground-truth dataset would be required for formal validation.

---

## Persistence Analysis

A hotspot that appears repeatedly in the same geographical area may represent a persistent thermal source.

The system performs spatial clustering and historical analysis to identify repeated detections.

Persistence information is then used as an additional feature for classification and priority assessment.

---

## Priority Assessment

After classification, the system calculates an operational priority score using factors such as:

- AI classification
- Fire Radiative Power (FRP)
- Number of detections
- Number of active days
- Persistence
- Nearby industrial context

The resulting priority levels are:

- **High**
- **Medium**
- **Low**

The priority score is intended as a decision-support indicator and is not a direct measurement of physical danger.

---

## Alert System

The system generates three alert categories:

### Critical

Generated when an event is classified as Industrial and has High priority.

### Warning

Generated when an event is classified as Industrial and meets additional persistence or priority conditions.

### Normal

Used for other detected events that do not meet the Critical or Warning conditions.

---

## GIS Dashboard

A web-based dashboard is developed using **Flask** and **Folium**.

The dashboard provides:

- Thermal hotspot visualization
- Industrial/Agricultural/Natural classification
- Priority levels
- Alert information
- Hotspot details
- Interactive maps
- Classification charts
- Priority charts
- Alert statistics
- Downloadable results

Users can investigate individual hotspots and view their geographic context.

---

## Technologies Used

### Programming

- Python
- HTML
- CSS
- JavaScript

### Backend

- Flask
- Pandas
- NumPy

### Geospatial Processing

- GeoPandas
- Rasterio
- Shapely
- Folium

### Machine Learning

- Scikit-learn
- Random Forest
- Median Imputation

### Visualization

- Folium
- Chart.js
- HTML/CSS/JavaScript

### External Data

- NASA FIRMS
- ESA WorldCover
- OpenStreetMap
- Overpass API

---

## Project Structure

```text
industrial-fire-monitor/
│
├── data/
│   ├── FIRMS data
│   ├── WorldCover data
│   ├── feature datasets
│   ├── predictions
│   ├── risk assessment
│   └── alerts
│
├── model/
│   └── industrial_fire_model.pkl
│
├── processing/
│   ├── FIRMS processing
│   ├── OSM processing
│   ├── WorldCover processing
│   ├── persistence analysis
│   ├── feature engineering
│   ├── model training
│   ├── prediction
│   ├── risk assessment
│   └── alert generation
│
├── static/
│   └── dashboard_map.html
│
├── templates/
│   ├── index.html
│   ├── map.html
│   └── hotspot.html
│
├── app.py
│
└── README.md
