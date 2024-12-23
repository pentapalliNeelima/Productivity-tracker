import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# SQLite Database Setup
def create_connection():
    conn = sqlite3.connect('time_tracker.db')
    return conn

def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            time_spent REAL,
            description TEXT,
            activity_type TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Function to insert activity
def add_activity(date, time_spent, description, activity_type):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO activities (date, time_spent, description, activity_type)
        VALUES (?, ?, ?, ?)
    ''', (date, time_spent, description, activity_type))
    conn.commit()
    conn.close()

# Function to delete an activity
def delete_activity(activity_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM activities WHERE id = ?', (activity_id,))
    conn.commit()
    conn.close()

# Function to get activities by date
def get_activities_by_date(date):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM activities WHERE date = ? ORDER BY id ASC', (date,))
    activities = cursor.fetchall()
    conn.close()
    return activities

# App Layout
def main():
    st.title("Time Tracker - Track Your Productivity")

    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        menu = st.radio("Go to", ["Add Activity", "View Activities", "Delete Activity", "Activity Analysis"])

    # Create table if not exists
    create_table()

    if menu == "Add Activity":
        st.header("Track Your Activity")
        with st.form(key="activity_form"):
            date = st.date_input("Date", value=datetime.today())
            hours_spent = st.number_input("Hours Spent", min_value=0, step=1)
            minutes_spent = st.number_input("Minutes Spent", min_value=0, max_value=59, step=1)
            description = st.text_input("Activity Description")
            activity_type = st.selectbox("Activity Type", ["Productive", "Wasteful"])
            
            submit_button = st.form_submit_button("Add Activity")
            if submit_button:
                # Check if description is empty
                if not description.strip():
                    st.error("Activity Description is mandatory. Please provide a description.")
                else:
                    # Convert hours and minutes into fractional hours
                    time_spent = hours_spent + (minutes_spent / 60)
                    add_activity(str(date), time_spent, description, activity_type)
                    st.success("Activity Added Successfully")

    elif menu == "View Activities":
        st.header("View All Activities")
        selected_date = st.date_input("Select a Date to View Activities")
        activities = get_activities_by_date(str(selected_date))
        if activities:
            df = pd.DataFrame(activities, columns=["ID", "Date", "Time Spent", "Description", "Activity Type"])
            st.dataframe(df)
        else:
            st.info("No activities found for the selected date. Start tracking your time.")

    elif menu == "Delete Activity":
        st.header("Delete an Activity")
        selected_date = st.date_input("Select a Date to Delete Activities")
        activities = get_activities_by_date(str(selected_date))
        if activities:
            df = pd.DataFrame(activities, columns=["ID", "Date", "Time Spent", "Description", "Activity Type"])
            activity_ids = df["ID"].tolist()
            activity_desc = df.apply(lambda row: f"{row['Date']} - {row['Description']} ({row['Activity Type']})", axis=1).tolist()
            
            selected_activity = st.selectbox("Select Activity to Delete", activity_desc)
            selected_index = activity_desc.index(selected_activity)
            selected_activity_id = activity_ids[selected_index]

            if st.button("Delete Activity"):
                delete_activity(selected_activity_id)
                st.success("Activity Deleted Successfully")
        else:
            st.info("No activities found for the selected date to delete.")

    elif menu == "Activity Analysis":
        st.header("Productivity & Waste Analysis by Date")
        selected_date = st.date_input("Select a Date to Analyze")
        activities = get_activities_by_date(str(selected_date))
        if activities:
            df = pd.DataFrame(activities, columns=["ID", "Date", "Time Spent", "Description", "Activity Type"])
            df["Time Spent"] = pd.to_numeric(df["Time Spent"])

            # Calculate total time spent for each activity type
            activity_summary = df.groupby("Activity Type")["Time Spent"].sum()

            # Define custom colors for the pie chart
            colors = {"Productive": "green", "Wasteful": "red"}

            # Plot Pie Chart for Activity Type Distribution
            fig = px.pie(
                activity_summary,
                names=activity_summary.index,
                values=activity_summary.values,
                title=f"Productivity vs Wasteful Activities for {selected_date}",
                labels={"index": "Activity Type", "values": "Time Spent"},
                color=activity_summary.index,  # Map colors to activity types
                color_discrete_map=colors
            )
            st.plotly_chart(fig)

            # Plot Bar Chart for Daily Activity Summary
            fig = go.Figure(data=[
                go.Bar(
                    x=activity_summary.index,
                    y=activity_summary.values,
                    text=activity_summary.values,
                    textposition='auto',
                    marker_color=["green" if t == "Productive" else "red" for t in activity_summary.index]
                )
            ])
            fig.update_layout(title="Time Spent by Activity Type", xaxis_title="Activity Type", yaxis_title="Time Spent (Hours)")
            st.plotly_chart(fig)
        else:
            st.info("No activities found for the selected date to analyze.")

if __name__ == "__main__":
    main()
