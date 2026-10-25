import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import folium_static
from data_parser import parse_timeline_data
import location_manager

st.set_page_config(page_title="Timeline Visualizer", layout="wide")

def load_data(file):
    try:
        json_data = json.load(file)
        df = parse_timeline_data(json_data)
        return df
    except Exception as e:
        st.error(f"Error parsing file: {e}")
        return None

def dashboard_view(df):
    st.header("Dashboard")

    # --- Filters ---
    st.sidebar.header("Filters")

    activity_types = df['activity_type'].dropna().unique().tolist()
    default_activities = ["IN_PASSENGER_VEHICLE"] if "IN_PASSENGER_VEHICLE" in activity_types else activity_types
    selected_activities = st.sidebar.multiselect(
        "Activity Types",
        options=activity_types,
        default=default_activities
    )

    min_dist = float(df['distance_km'].min())
    max_dist = float(df['distance_km'].max())
    if pd.isna(min_dist) or pd.isna(max_dist):
        min_dist, max_dist = 0.0, 100.0

    distance_range = st.sidebar.slider(
        "Distance Range (km)",
        min_value=0.0,
        max_value=max_dist + 10.0,
        value=(0.0, 100.0 if max_dist > 100 else max_dist)
    )

    filtered_df = df[
        (df['activity_type'].isin(selected_activities)) &
        (df['distance_km'] >= distance_range[0]) &
        (df['distance_km'] <= distance_range[1])
    ].copy()

    # KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Journeys", len(filtered_df))
    col2.metric("Total Distance (km)", round(filtered_df['distance_km'].sum(), 2))
    col3.metric("Avg Distance (km)", round(filtered_df['distance_km'].mean(), 2) if not filtered_df.empty else 0)

    if not filtered_df.empty:
        # Resolve names with the latest dict
        locations_dict = location_manager.load_locations()
        filtered_df['start_name'] = filtered_df['start_place_id'].apply(lambda x: locations_dict.get(x, x if x else "Unknown Start"))
        filtered_df['end_name'] = filtered_df['end_place_id'].apply(lambda x: locations_dict.get(x, x if x else "Unknown End"))

        # --- Visualizations ---
        st.subheader("Top Destinations")
        top_dests = filtered_df['end_name'].value_counts().head(10)
        st.bar_chart(top_dests)

        st.subheader("Most Frequent Routes")
        filtered_df['route'] = filtered_df['start_name'] + " ➔ " + filtered_df['end_name']
        top_routes = filtered_df['route'].value_counts().head(10)
        st.bar_chart(top_routes)

        # --- Map ---
        st.subheader("Journey Map")
        # Group by location for map
        grouped = filtered_df.groupby(['end_lat', 'end_lng', 'end_name', 'end_place_id']).size().reset_index(name='visits')

        if not grouped.empty:
            center_lat = grouped['end_lat'].mean()
            center_lng = grouped['end_lng'].mean()

            m = folium.Map(location=[center_lat, center_lng], zoom_start=10)

            for _, row in grouped.iterrows():
                popup_text = f"<b>{row['end_name']}</b><br>Visits: {row['visits']}<br>Place ID: {row['end_place_id']}"
                folium.Marker(
                    location=[row['end_lat'], row['end_lng']],
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=row['end_name']
                ).add_to(m)

            folium_static(m, width=1000, height=500)
        else:
            st.info("No valid coordinates to display on the map.")

    else:
        st.warning("No data matching filters.")

def location_manager_view(df):
    st.header("Location Manager")

    locations_dict = location_manager.load_locations()
    all_places = pd.concat([df['start_place_id'], df['end_place_id']]).dropna()
    unknown_places = all_places[~all_places.isin(locations_dict.keys())]
    unknown_counts = unknown_places.value_counts()

    if not unknown_counts.empty:
        st.subheader("Name an Unknown Location")
        top_unnamed = unknown_counts.head(50).index.tolist()

        selected_unnamed_place = st.selectbox(
            "Select Place ID",
            options=top_unnamed,
            format_func=lambda x: f"{x} ({unknown_counts[x]} visits)"
        )

        # Find coordinates for the selected place
        place_coords = df[(df['start_place_id'] == selected_unnamed_place) | (df['end_place_id'] == selected_unnamed_place)]

        lat, lng = None, None
        if not place_coords.empty:
            # Check ends first, then starts
            end_match = place_coords[place_coords['end_place_id'] == selected_unnamed_place]
            if not end_match.empty and pd.notna(end_match.iloc[0]['end_lat']):
                lat = end_match.iloc[0]['end_lat']
                lng = end_match.iloc[0]['end_lng']
            else:
                start_match = place_coords[place_coords['start_place_id'] == selected_unnamed_place]
                if not start_match.empty and pd.notna(start_match.iloc[0]['start_lat']):
                    lat = start_match.iloc[0]['start_lat']
                    lng = start_match.iloc[0]['start_lng']

        col1, col2 = st.columns([1, 2])

        with col1:
            new_name = st.text_input("Custom Name")
            if st.button("Save Name"):
                if new_name and selected_unnamed_place:
                    location_manager.save_location(selected_unnamed_place, new_name)
                    st.success(f"Saved: {new_name}")
                    st.rerun()
                else:
                    st.error("Provide a name.")

        with col2:
            if lat is not None and lng is not None:
                st.write("**Location Preview**")
                m = folium.Map(location=[lat, lng], zoom_start=16)
                folium.Marker(
                    location=[lat, lng],
                    popup=f"Place ID: {selected_unnamed_place}"
                ).add_to(m)
                folium_static(m, width=600, height=400)
            else:
                st.info("No coordinates available for this location to display on the map.")
    else:
        st.info("All visited locations have custom names!")

    st.subheader("Manage Saved Locations")
    if locations_dict:
        saved_df = pd.DataFrame(list(locations_dict.items()), columns=['Place ID', 'Custom Name'])
        st.dataframe(saved_df, use_container_width=True)
    else:
        st.write("No locations saved yet.")


def main():
    st.title("Google Maps Timeline Analytics")

    st.sidebar.header("Upload Timeline Data")
    uploaded_file = st.sidebar.file_uploader("Upload semanticSegments JSON", type=['json'])

    if uploaded_file is not None:
        df = load_data(uploaded_file)
        if df is not None and not df.empty:
            st.sidebar.success(f"Loaded {len(df)} activities")

            # --- Navigation ---
            st.sidebar.header("Navigation")
            page = st.sidebar.radio("Go to", ["Dashboard", "Location Manager"])

            if page == "Dashboard":
                dashboard_view(df)
            elif page == "Location Manager":
                location_manager_view(df)

    else:
        st.info("Please upload a JSON file to get started.")

if __name__ == '__main__':
    main()
