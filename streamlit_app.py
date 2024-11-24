import streamlit as st
import mysql.connector
from mysql.connector import Error
from time import sleep
import hashlib

#========================================
# (1) Test Connection
def create_connection():
    config = {
        'user': st.secrets["mysql"]["user"],
        'password': st.secrets["mysql"]["password"],
        'host': st.secrets["mysql"]["host"],
        'port': st.secrets["mysql"]["port"],
        'database': st.secrets["mysql"]["database"]
    }
    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            return conn
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

def close_connection(conn):
    if conn and conn.is_connected():
        conn.close()

#========================================
# (2) Login Logic
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def try_login(input_username, input_password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM student_login WHERE student_id = %s ", (input_username,))
    result = cursor.fetchone()
    if result:
        stored_password = result[0]  # Get the stored password
        if hash_password(input_password) == stored_password:
            st.session_state.logged_in = True  # Set login state to True
            st.success("Logged in!")
            sleep(1)
            st.experimental_rerun()  # Rerun the app to show the sidebar
        else:
            st.error("Your username or password is incorrect")
    else:
        st.error("Your username or password is incorrect")

    cursor.close()
    conn.close()

#========================================
# (3) Login Page
def login():
    input_username = st.text_input("Username", key="username")
    input_password = st.text_input("Password", key="password", type="password")
    if st.button("Login"):
        try_login(input_username, input_password)

#========================================
# (4) Main logic for app
def main():
    # Initialize session state for login status if not already initialized
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False  # Default to False if not logged in

    # Disable sidebar during the login process
    if not st.session_state.logged_in:
        st.set_page_config(page_title="Login", layout="centered", initial_sidebar_state="collapsed")
        st.title("Login Page")
        login()
    else:
        # Enable sidebar once logged in
        st.set_page_config(page_title="Main Page", layout="wide", initial_sidebar_state="expanded")

        # Once logged in, show the sidebar
        with st.sidebar:
            st.title("Sidebar")
            st.write("This is a sidebar visible after login.")

        # Main content after login
        st.title("SCENARY Backend")
        st.write("Welcome to the main page!")

#========================================
# Run the app
if __name__ == "__main__":
    main()

#========================================
# Test Database Connection
st.write("TEST Connection") 
conn = create_connection()
if conn:
    st.write("Connected to MySQL database")
    cursor = conn.cursor()
else:
    st.error("Failed to connect to the database.")
st.write("Session State:", st.session_state)
close_connection(conn)
st.experimental_rerun()