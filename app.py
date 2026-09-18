from flask import Flask, render_template, request, send_file
import pandas as pd
import folium
from folium.plugins import Fullscreen
import os
import json
import math

app = Flask(__name__)


# ============================================================
# SAFE NUMBER
# ============================================================

def safe_float(value, default=0.0):

    try:

        if pd.isna(value):
            return default

        if isinstance(value, str):

            value = value.strip()
            value = value.replace("%", "")
            value = value.replace(",", "")

        number = float(value)

        if not math.isfinite(number):
            return default

        return number

    except:

        return default


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    predictions_file = "data/predictions.csv"
    risk_file = "data/risk_assessment.csv"
    alerts_file = "data/alerts.csv"

    if not os.path.exists(predictions_file):

        raise FileNotFoundError(
            "data/predictions.csv not found. "
            "Run: python processing/predict_all.py"
        )

    if not os.path.exists(risk_file):

        raise FileNotFoundError(
            "data/risk_assessment.csv not found. "
            "Run: python processing/create_risk_assessment.py"
        )

    if not os.path.exists(alerts_file):

        raise FileNotFoundError(
            "data/alerts.csv not found. "
            "Run: python processing/create_alerts.py"
        )

    predictions = pd.read_csv(
        predictions_file
    )

    risk = pd.read_csv(
        risk_file
    )

    alerts = pd.read_csv(
        alerts_file
    )

    # --------------------------------------------------------
    # Normalize hotspot ID
    # --------------------------------------------------------

    for df in [predictions, risk, alerts]:

        if "hotspot_id" in df.columns:

            df["hotspot_id"] = pd.to_numeric(
                df["hotspot_id"],
                errors="coerce"
            )

    # --------------------------------------------------------
    # Risk columns
    # --------------------------------------------------------

    risk_columns = [
        "hotspot_id",
        "priority_score",
        "priority_level",
        "priority_reasons"
    ]

    risk_columns = [
        c for c in risk_columns
        if c in risk.columns
    ]

    risk_small = risk[
        risk_columns
    ].copy()

    # --------------------------------------------------------
    # Alert columns
    # --------------------------------------------------------

    alert_columns = [
        "hotspot_id",
        "alert_level",
        "alert_message",
        "alert_generated_at"
    ]

    alert_columns = [
        c for c in alert_columns
        if c in alerts.columns
    ]

    alerts_small = alerts[
        alert_columns
    ].copy()

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    data = predictions.merge(
        risk_small,
        on="hotspot_id",
        how="left"
    )

    data = data.merge(
        alerts_small,
        on="hotspot_id",
        how="left"
    )

    # --------------------------------------------------------
    # FIND PROBABILITY
    # --------------------------------------------------------

    probability_names = [

        "prediction_probability",

        "probability",

        "confidence_probability",

        "ai_probability",

        "prediction_confidence",

        "confidence"
    ]

    probability_column = None

    for name in probability_names:

        if name in data.columns:

            probability_column = name
            break

    # --------------------------------------------------------
    # Parse probability correctly
    # --------------------------------------------------------

    if probability_column is not None:

        def parse_probability(value):

            try:

                if pd.isna(value):
                    return 0.0

                text = str(value).strip()

                # Remove percentage sign
                if "%" in text:

                    number = float(
                        text.replace("%", "")
                    )

                    return max(
                        0.0,
                        min(
                            number / 100.0,
                            1.0
                        )
                    )

                number = float(
                    text.replace(",", "")
                )

                # 91 -> 0.91
                if number > 1:

                    number = number / 100.0

                return max(
                    0.0,
                    min(
                        number,
                        1.0
                    )
                )

            except:

                return 0.0

        data[
            "prediction_probability"
        ] = data[
            probability_column
        ].apply(
            parse_probability
        )

    else:

        data[
            "prediction_probability"
        ] = 0.0

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    defaults = {

        "ai_prediction": "Unknown",

        "priority_score": 0,

        "priority_level": "Low",

        "priority_reasons": "",

        "alert_level": "NORMAL",

        "alert_message": "",

        "alert_generated_at": "",

        "latitude": 0,

        "longitude": 0,

        "brightness": 0,

        "frp": 0,

        "detections": 0,

        "active_days": 0,

        "persistent": 0,

        "landcover_type": "Unknown",

        "osm_context": "No OSM context",

        "acq_date": "",

        "acq_time": ""
    }

    for column, default in defaults.items():

        if column not in data.columns:

            data[column] = default

        data[column] = data[
            column
        ].fillna(default)

    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    numeric_columns = [

        "hotspot_id",

        "latitude",

        "longitude",

        "brightness",

        "frp",

        "detections",

        "active_days",

        "persistent",

        "priority_score",

        "prediction_probability"
    ]

    for column in numeric_columns:

        data[column] = data[
            column
        ].apply(
            lambda x: safe_float(x)
        )

    return data


# ============================================================
# FILTERS
# ============================================================

def get_filtered_data(data):

    selected_class = request.args.get(
        "classification",
        "All"
    )

    selected_priority = request.args.get(
        "priority",
        "All"
    )

    selected_alert = request.args.get(
        "alert",
        "All"
    )

    filtered = data.copy()

    if selected_class != "All":

        filtered = filtered[
            filtered[
                "ai_prediction"
            ].astype(str).str.lower()
            ==
            selected_class.lower()
        ]

    if selected_priority != "All":

        filtered = filtered[
            filtered[
                "priority_level"
            ].astype(str).str.lower()
            ==
            selected_priority.lower()
        ]

    if selected_alert != "All":

        filtered = filtered[
            filtered[
                "alert_level"
            ].astype(str).str.lower()
            ==
            selected_alert.lower()
        ]

    return (
        filtered,
        selected_class,
        selected_priority,
        selected_alert
    )


# ============================================================
# CREATE GIS MAP
# ============================================================

def create_gis_map(data):

    if len(data) > 0:

        center_lat = safe_float(
            data["latitude"].mean(),
            20.5937
        )

        center_lon = safe_float(
            data["longitude"].mean(),
            78.9629
        )

    else:

        center_lat = 20.5937
        center_lon = 78.9629

    m = folium.Map(

        location=[
            center_lat,
            center_lon
        ],

        zoom_start=6,

        control_scale=True
    )

    # --------------------------------------------------------
    # Satellite
    # --------------------------------------------------------

    folium.TileLayer(

        tiles=(
            "https://server.arcgisonline.com/"
            "ArcGIS/rest/services/"
            "World_Imagery/"
            "MapServer/tile/{z}/{y}/{x}"
        ),

        attr="Esri World Imagery",

        name="Satellite",

        overlay=False,

        control=True

    ).add_to(m)

    # --------------------------------------------------------
    # OpenStreetMap
    # --------------------------------------------------------

    folium.TileLayer(

        "OpenStreetMap",

        name="OpenStreetMap",

        overlay=False,

        control=True

    ).add_to(m)

    # --------------------------------------------------------
    # Classification colors
    # --------------------------------------------------------

    colors = {

        "Industrial": "red",

        "Agricultural": "orange",

        "Natural": "green",

        "Unknown": "gray"
    }

    # --------------------------------------------------------
    # Add hotspots
    # --------------------------------------------------------

    for _, row in data.iterrows():

        latitude = safe_float(
            row["latitude"]
        )

        longitude = safe_float(
            row["longitude"]
        )

        hotspot_id = int(
            safe_float(
                row["hotspot_id"]
            )
        )

        classification = str(
            row["ai_prediction"]
        )

        priority = str(
            row["priority_level"]
        )

        alert = str(
            row["alert_level"]
        )

        probability = safe_float(
            row["prediction_probability"]
        )

        score = safe_float(
            row["priority_score"]
        )

        brightness = safe_float(
            row["brightness"]
        )

        frp = safe_float(
            row["frp"]
        )

        detections = int(
            safe_float(
                row["detections"]
            )
        )

        active_days = int(
            safe_float(
                row["active_days"]
            )
        )

        landcover = str(
            row["landcover_type"]
        )

        color = colors.get(
            classification,
            "gray"
        )

        # ----------------------------------------------------
        # Popup
        # ----------------------------------------------------

        popup_html = f"""

        <div style="
            font-family:Arial;
            width:290px;
        ">

            <h3>
                🔥 Hotspot #{hotspot_id}
            </h3>

            <b>AI Classification:</b>
            {classification}

            <br><br>

            <b>Alert:</b>
            {alert}

            <br>

            <b>Priority:</b>
            {priority}

            <br>

            <b>Priority Score:</b>
            {score:.1f}

            <br>

            <b>AI Probability:</b>
            {probability * 100:.1f}%

            <br><br>

            <b>Brightness:</b>
            {brightness:.2f}

            <br>

            <b>FRP:</b>
            {frp:.2f}

            <br>

            <b>Land Cover:</b>
            {landcover}

            <br>

            <b>Detections:</b>
            {detections}

            <br>

            <b>Active Days:</b>
            {active_days}

            <br><br>

            <a
                href="/hotspot/{hotspot_id}"
                target="_blank"
                style="
                    display:inline-block;
                    padding:9px 13px;
                    background:#111827;
                    color:white;
                    text-decoration:none;
                    border-radius:6px;
                "
            >
                Open Full Investigation
            </a>

        </div>

        """

        folium.CircleMarker(

            location=[
                latitude,
                longitude
            ],

            radius=7,

            color=color,

            fill=True,

            fill_color=color,

            fill_opacity=0.85,

            popup=folium.Popup(
                popup_html,
                max_width=350
            ),

            tooltip=(
                f"Hotspot #{hotspot_id} | "
                f"{classification}"
            )

        ).add_to(m)

    # --------------------------------------------------------
    # Fullscreen
    # --------------------------------------------------------

    Fullscreen(
        position="topright"
    ).add_to(m)

    # --------------------------------------------------------
    # Layer control
    # --------------------------------------------------------

    folium.LayerControl().add_to(m)

    # --------------------------------------------------------
    # Legend
    # --------------------------------------------------------

    legend = """

    <div style="
        position:fixed;
        bottom:30px;
        left:30px;
        z-index:9999;
        background:white;
        padding:14px;
        border-radius:8px;
        box-shadow:0 2px 8px rgba(0,0,0,.25);
        font-family:Arial;
        font-size:13px;
    ">

        <b>AI Classification</b>

        <br><br>

        <span style="color:red;">
            ●
        </span>
        Industrial

        <br>

        <span style="color:orange;">
            ●
        </span>
        Agricultural

        <br>

        <span style="color:green;">
            ●
        </span>
        Natural

        <br>

        <span style="color:gray;">
            ●
        </span>
        Unknown

    </div>

    """

    m.get_root().html.add_child(
        folium.Element(
            legend
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    os.makedirs(
        "static",
        exist_ok=True
    )

    m.save(
        "static/dashboard_map.html"
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def index():

    data = load_data()

    (
        filtered,
        selected_class,
        selected_priority,
        selected_alert
    ) = get_filtered_data(data)

    # --------------------------------------------------------
    # ALWAYS CREATE MAP
    # This fixes the "Not Found" map problem.
    # --------------------------------------------------------

    create_gis_map(filtered)

    # --------------------------------------------------------
    # Classification counts
    # --------------------------------------------------------

    agricultural_count = int(
        (
            filtered["ai_prediction"]
            == "Agricultural"
        ).sum()
    )

    industrial_count = int(
        (
            filtered["ai_prediction"]
            == "Industrial"
        ).sum()
    )

    natural_count = int(
        (
            filtered["ai_prediction"]
            == "Natural"
        ).sum()
    )

    # --------------------------------------------------------
    # Priority counts
    # --------------------------------------------------------

    low_count = int(
        (
            filtered["priority_level"]
            == "Low"
        ).sum()
    )

    medium_count = int(
        (
            filtered["priority_level"]
            == "Medium"
        ).sum()
    )

    high_count = int(
        (
            filtered["priority_level"]
            == "High"
        ).sum()
    )

    # --------------------------------------------------------
    # Alert counts
    # --------------------------------------------------------

    normal_count = int(
        (
            filtered["alert_level"]
            == "NORMAL"
        ).sum()
    )

    warning_count = int(
        (
            filtered["alert_level"]
            == "WARNING"
        ).sum()
    )

    critical_count = int(
        (
            filtered["alert_level"]
            == "CRITICAL"
        ).sum()
    )

    # --------------------------------------------------------
    # Alerts
    # --------------------------------------------------------

    critical_alerts = filtered[
        filtered["alert_level"]
        == "CRITICAL"
    ].sort_values(
        "priority_score",
        ascending=False
    )

    warning_alerts = filtered[
        filtered["alert_level"]
        == "WARNING"
    ].sort_values(
        "priority_score",
        ascending=False
    )

    recent_alerts = filtered[
        filtered["alert_level"].isin(
            [
                "CRITICAL",
                "WARNING"
            ]
        )
    ].sort_values(
        "priority_score",
        ascending=False
    ).head(10)

    # --------------------------------------------------------
    # Convert records safely
    # --------------------------------------------------------

    records = filtered.sort_values(
        "priority_score",
        ascending=False
    )

    records_json = json.loads(
        records.to_json(
            orient="records"
        )
    )

    critical_json = json.loads(
        critical_alerts.to_json(
            orient="records"
        )
    )

    warning_json = json.loads(
        warning_alerts.to_json(
            orient="records"
        )
    )

    recent_json = json.loads(
        recent_alerts.to_json(
            orient="records"
        )
    )

    # --------------------------------------------------------
    # Charts
    # --------------------------------------------------------

    classification_labels = json.dumps(
        [
            "Agricultural",
            "Industrial",
            "Natural"
        ]
    )

    classification_values = json.dumps(
        [
            agricultural_count,
            industrial_count,
            natural_count
        ]
    )

    priority_labels = json.dumps(
        [
            "Low",
            "Medium",
            "High"
        ]
    )

    priority_values = json.dumps(
        [
            low_count,
            medium_count,
            high_count
        ]
    )

    alert_labels = json.dumps(
        [
            "NORMAL",
            "WARNING",
            "CRITICAL"
        ]
    )

    alert_values = json.dumps(
        [
            normal_count,
            warning_count,
            critical_count
        ]
    )

    # --------------------------------------------------------
    # Render
    # --------------------------------------------------------

    return render_template(

        "index.html",

        total=int(
            len(filtered)
        ),

        agricultural_count=(
            agricultural_count
        ),

        industrial_count=(
            industrial_count
        ),

        natural_count=(
            natural_count
        ),

        low_count=low_count,

        medium_count=medium_count,

        high_count=high_count,

        normal_count=normal_count,

        warning_count=warning_count,

        critical_count=critical_count,

        critical_alerts=critical_json,

        warning_alerts=warning_json,

        alerts=recent_json,

        records=records_json,

        classification_labels=(
            classification_labels
        ),

        classification_values=(
            classification_values
        ),

        priority_labels=(
            priority_labels
        ),

        priority_values=(
            priority_values
        ),

        alert_labels=alert_labels,

        alert_values=alert_values,

        selected_class=selected_class,

        selected_priority=selected_priority,

        selected_alert=selected_alert
    )


# ============================================================
# GIS MAP PAGE
# ============================================================

@app.route("/map")
def map_view():

    data = load_data()

    (
        filtered,
        selected_class,
        selected_priority,
        selected_alert
    ) = get_filtered_data(data)

    create_gis_map(
        filtered
    )

    return render_template(

        "map.html",

        selected_class=selected_class,

        selected_priority=selected_priority,

        selected_alert=selected_alert
    )


# ============================================================
# HOTSPOT INVESTIGATION
# ============================================================

@app.route("/hotspot/<int:hotspot_id>")
def hotspot(hotspot_id):

    data = load_data()

    result = data[
        data["hotspot_id"]
        == hotspot_id
    ]

    if result.empty:

        return (
            f"Hotspot #{hotspot_id} not found",
            404
        )

    hotspot_data = result.iloc[
        0
    ].to_dict()

    return render_template(

        "hotspot.html",

        hotspot=hotspot_data
    )


# ============================================================
# DOWNLOAD COMPLETE RESULTS
# ============================================================

@app.route("/download")
def download_results():

    data = load_data()

    output = (
        "data/final_results.csv"
    )

    data.to_csv(
        output,
        index=False
    )

    return send_file(

        output,

        as_attachment=True,

        download_name=(
            "industrial_fire_detection_results.csv"
        ),

        mimetype="text/csv"
    )


# ============================================================
# DOWNLOAD ALERTS
# ============================================================

@app.route("/download-alerts")
def download_alerts():

    file = (
        "data/alerts.csv"
    )

    if not os.path.exists(file):

        return (
            "alerts.csv not found",
            404
        )

    return send_file(

        file,

        as_attachment=True,

        download_name=(
            "industrial_fire_alerts.csv"
        ),

        mimetype="text/csv"
    )


# ============================================================
# DOWNLOAD RISK
# ============================================================

@app.route("/download-risk")
def download_risk():

    file = (
        "data/risk_assessment.csv"
    )

    if not os.path.exists(file):

        return (
            "risk_assessment.csv not found",
            404
        )

    return send_file(

        file,

        as_attachment=True,

        download_name=(
            "industrial_fire_risk_assessment.csv"
        ),

        mimetype="text/csv"
    )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True
    )