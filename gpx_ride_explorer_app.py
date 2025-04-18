"""gpx_ride_explorer_app.py

Interactive Streamlit application to explore data from cycling GPX files.

Features
--------
* Upload any .gpx file (defaults to a sample if none uploaded when running locally)
* Parses time, latitude, longitude, elevation, heart‑rate, power, cadence
* Displays:
    – Interactive Plotly line chart (choose which series to plot)
    – Smoothed data with adjustable window (sidebar)
    – Map of the route
    – Key ride summary metrics (distance, duration, average HR / power)
* All charts are zoomable & hoverable.
* Requires: streamlit, gpxpy, pandas, numpy, plotly

Run locally:
-------------
pip install streamlit gpxpy pandas numpy plotly
streamlit run gpx_ride_explorer_app.py
"""

from __future__ import annotations

from datetime import timezone
from math import asin, cos, radians, sin, sqrt

import io
import typing as t

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great‑circle distance in metres between two lat/lon points."""
    R = 6_371_000  # Earth radius in metres
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * R * asin(sqrt(a))


@st.cache_data(show_spinner="Parsing GPX …")
def parse_gpx(file_like: io.BufferedIOBase) -> pd.DataFrame:
    """
    Robust GPX parser that extracts *all* available metrics (power, HR, cadence)
    directly from the XML, bypassing gpxpy’s limited extension handling.

    Returns a tidy DataFrame indexed by local time with columns:
    latitude, longitude, elevation, heart_rate, power, cadence, segment_dist_m, cum_dist_km
    """
    import xml.etree.ElementTree as ET

    xml_bytes = file_like.read()
    if isinstance(xml_bytes, bytes):
        xml_str = xml_bytes.decode("utf-8", errors="ignore")
    else:
        xml_str = xml_bytes

    root = ET.fromstring(xml_str)

    # Resolve namespaces -> strip them for easier matching
    ns_map = {k if k else "ns": v for k, v in root.attrib.items() if k.startswith("xmlns")}
    def strip(tag: str) -> str:
        return tag.split("}")[-1]  # drop namespace URI if present

    rows: list[dict[str, t.Any]] = []

    # Walk all trackpoints
    for trkpt in root.iter():
        if strip(trkpt.tag) != "trkpt":
            continue

        lat = float(trkpt.attrib.get("lat"))
        lon = float(trkpt.attrib.get("lon"))
        ele = None
        time_str = None
        hr = power = cad = None

        # Inspect children
        for child in trkpt:
            tag = strip(child.tag)
            if tag == "ele":
                ele = float(child.text)
            elif tag == "time":
                time_str = child.text.strip()
            elif tag == "extensions":
                # search recursively for metrics
                for el in child.iter():
                    base = strip(el.tag).lower()
                    text = (el.text or "").strip()
                    if not text:
                        continue
                    if base in {"hr", "heartrate"} and hr is None:
                        hr = int(float(text))
                    elif base == "power" and power is None:
                        power = int(float(text))
                    elif base in {"cad", "cadence"} and cad is None:
                        cad = int(float(text))

        if not time_str:
            continue  # skip malformed points
        ts = pd.to_datetime(time_str).tz_convert(None)  # naive local time

        rows.append(
            {
                "time": ts,
                "latitude": lat,
                "longitude": lon,
                "elevation": ele,
                "heart_rate": hr,
                "power": power,
                "cadence": cad,
            }
        )

    if not rows:
        raise ValueError("No <trkpt> elements found – is this a valid GPX file?")

    df = pd.DataFrame(rows).sort_values("time").set_index("time")

    # Distance calculations
    dists = [0.0]
    for i in range(1, len(df)):
        d = haversine(
            df.iloc[i - 1].latitude,
            df.iloc[i - 1].longitude,
            df.iloc[i].latitude,
            df.iloc[i].longitude,
        )
        dists.append(d)
    df["segment_dist_m"] = dists
    df["cum_dist_km"] = np.cumsum(dists) / 1_000
    
    # Ensure numeric dtype (replace Python None with NaN)
    for col in ("heart_rate", "power", "cadence"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    return df


def plot_time_series(df: pd.DataFrame, cols: list[str]):
    """
    Plot selected data series using long‑form tidy data so Plotly Express
    handles mixed numeric dtypes gracefully (fixes ValueError about wide‑form).
    """
    if not cols:
        return  # nothing to plot

    # Convert to numeric and build tidy DataFrame
    df_long = (
        df[cols]
        .apply(pd.to_numeric, errors="coerce")
        .reset_index()
        .melt(id_vars="time", value_vars=cols, var_name="metric", value_name="value")
        .dropna(subset=["value"])
    )

    fig = px.line(
        df_long,
        x="time",
        y="value",
        color="metric",
        template="simple_white",
        labels={"time": "Time", "value": "", "metric": "Metric"},
    )

    fig.update_layout(legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)


def main():
    st.set_page_config(page_title="GPX Ride Explorer", layout="wide")
    st.title("🚴‍♂️ GPX Ride Explorer")

    st.sidebar.header("File Selection")
    gpx_file = st.sidebar.file_uploader("Upload a .gpx file", type="gpx")

    if gpx_file is None:
        st.info("Upload a GPX file via the sidebar to get started.")
        st.stop()

    df = parse_gpx(gpx_file)
    # --- Derived metrics for mapping ---
    df["time_diff_s"] = df.index.to_series().diff().dt.total_seconds()
    df.loc[df["time_diff_s"] == 0, "time_diff_s"] = np.nan
    df["speed_mps"] = df["segment_dist_m"] / df["time_diff_s"]
    df["speed_mph"] = df["speed_mps"] * 2.23694

    elev_diff = df["elevation"].diff()
    horiz = df["segment_dist_m"].replace(0, np.nan)
    df["grade_pct"] = (elev_diff / horiz) * 100

    st.success(f"Loaded {len(df):,} track points.")

    # --- Summary metrics ---
    st.subheader("Ride summary")
    cols1, cols2, cols3, cols4 = st.columns(4)
    total_km = df["cum_dist_km"].iloc[-1]
    total_mi = total_km * 0.621371
    duration_td = df.index[-1] - df.index[0]
    total_seconds = int(duration_td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    duration_str = f"{hours}h {minutes:02d}m"
    # cols1.metric("Distance (km)", f"{total_km:.2f}")
    cols1.metric("Distance (mi)", f"{total_mi:.2f}")
    cols2.metric("Duration", duration_str)
    if df["power"].notna().any():
        cols3.metric("Avg Power (W)", f"{df['power'].mean():.0f}")
    if df["heart_rate"].notna().any():
        cols4.metric("Avg HR (bpm)", f"{df['heart_rate'].mean():.0f}")

    # --- Map with color‑coded route ---
    st.subheader("Route map")
 
    map_metric = st.selectbox(
        "Color route by:",
        ("None", "Elevation gradient (%)", "Speed (mph)", "Heart rate (bpm)", "Power (W)"),
        index=0,
    )
 
    metric_col_map = {
        "Elevation gradient (%)": "grade_pct",
        "Speed (mph)": "speed_mph",
        "Heart rate (bpm)": "heart_rate",
        "Power (W)": "power",
    }
    color_col = metric_col_map.get(map_metric)
 
    map_df = df.copy()
    map_params = dict(
        lat="latitude",
        lon="longitude",
        zoom=10,
        height=600,
        hover_data={"speed_mph": True, "grade_pct": True, "heart_rate": True, "power": True},
    )
 
    if color_col:
        fig_map = px.scatter_mapbox(
            map_df,
            color=color_col,
            color_continuous_scale="Turbo",
            **map_params,
        )
    else:
        fig_map = px.scatter_mapbox(map_df, **map_params)
 
    fig_map.update_layout(mapbox_style="carto-positron", margin=dict(r=0, t=0, l=0, b=0))
    st.plotly_chart(fig_map, use_container_width=True, key="route_map")

    # --- Elevation profile ---
    if "elevation" in df.columns and df["elevation"].notna().any():
        st.subheader("Elevation profile")
        # Convert elevation to feet for plotting
        elev_df = df[["elevation"]].copy()
        elev_df["elevation_ft"] = elev_df["elevation"] * 3.28084
        fig_elev = px.line(
            elev_df.reset_index(),
            x="time",
            y="elevation_ft",
            labels={"time": "Time", "elevation_ft": "Elevation (ft)"},
            template="simple_white",
        )
        st.plotly_chart(fig_elev, use_container_width=True)

    # --- Interactive plots ---
    st.subheader("Interactive time‑series plots")
    metric_cols = ["power", "heart_rate", "cadence"]
    available_cols = [c for c in metric_cols if c in df.columns]
    default_cols = [c for c in ["power", "heart_rate"] if c in available_cols]

    selected = st.multiselect(
        "Choose data series to plot:", available_cols, default=default_cols
    )

    if not selected:
        st.warning("Select at least one series to plot.")
        pass  # plotting handled below
    else:
        df_metrics = df[selected]

    # --- Optional smoothing ---
    if selected:
        smooth_sec = st.sidebar.slider(
            "Smoothing window (seconds)", 0, 100, 0, step=5, key="smooth"
        )
        if smooth_sec > 0:
            df_metrics = df_metrics.rolling(f"{smooth_sec}s").mean()
        st.subheader("Interactive metrics plot")
        plot_time_series(df_metrics, selected)

    # --- Raw data inspection ---
    with st.expander("Show raw data"):
        # Show the first 50 rows *with at least one metric present*,
        # so the preview isn't filled with NaN values.
        preview = df[df[["power", "heart_rate", "cadence"]].notna().any(axis=1)].head(50)
        st.dataframe(preview)
        csv_data = df.to_csv(index=True).encode("utf-8")
        st.download_button(
            label="📥 Download full data as CSV",
            data=csv_data,
            mime="text/csv",
            file_name="ride_data.csv",
        )


if __name__ == "__main__":
    main()

