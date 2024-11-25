import streamlit as st
import mysql.connector
from mysql.connector import Error
from time import sleep
import hashlib
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode
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
        # if hash_password(input_password) == stored_password:
        if input_password == stored_password:
            st.session_state.logged_in = True  # Set login state to True
            st.success("Logged in!")
            sleep(1)
            # st.experimental_rerun()  # Rerun the app to show the sidebar
        else:
            st.error("Your username or password is incorrect")
    else:
        st.error("Your username or password is incorrect")

    cursor.close()
    conn.close()

#========================================
#1 ShowColumn
def showColumn(table_name):
    try:
        conn = create_connection()
        cursor = conn.cursor()
    
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()

        # Print only the column names
        List_column_name = [column[0] for column in columns]
        return List_column_name
        # return st.write(List_column_name)

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        close_connection(conn)

#2 Add DATA
def insert_data(table_name,values):
    try:
        conn = create_connection()
        cursor = conn.cursor()

        columns = showColumn(table_name)
        # print(columns)
        columns_str = ','.join(columns)
        placeholders = ','.join(['%s'] * len(values))
        
        # Execute the query with the provided values
        query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        cursor.execute(query, values)
        conn.commit()

        print(f"1 record inserted successfully into {table_name}")

    except mysql.connector.Error as error:
        print(f"Failed to insert data into MySQL table {table_name}: {error}")

    finally:
        close_connection(conn)

def insert_data_student(student_id,first_name,last_name,email,contact_number,address,register_date):
    insert_data("student",[student_id,first_name,last_name,email,contact_number,address,register_date])

def insert_data_enrollment(enrollment_id,student_id,course_id,semester,year,grade,enrollment_date):
    insert_data("enrollment",[enrollment_id,student_id,course_id,semester,year,grade,enrollment_date])

def insert_data_instructor(instructor_id,first_name,last_name,department_id,email,contact_number):
    insert_data("instructor",[instructor_id,first_name,last_name,department_id,email,contact_number])

def insert_data_course(course_id,course_name,credits,department_id,instructor_id):
    insert_data("course",[course_id,course_name,credits,department_id,instructor_id])

def insert_data_department(department_id,department_name):
    insert_data("department",[department_id,department_name])

#3 Del DATA
def delete_data(table_name, condition):
    try:
        # Establish connection to the database
        conn = create_connection()
        cursor = conn.cursor()

        # Create the delete query
        query = f"DELETE FROM {table_name} WHERE {condition}"
        
        # Execute the delete query
        cursor.execute(query)

        conn.commit()

        print(f"Record(s) deleted successfully from {table_name} where {condition}")

    except mysql.connector.Error as error:
        print(f"Failed to delete data from MySQL table {table_name}: {error}")

    finally:
        close_connection(conn)

#update
def update_data(table_name, updates, condition):
    try:
        conn = create_connection()
        cursor = conn.cursor()

        # Create the update query
        set_clause = ', '.join([f"{column} = %s" for column in updates.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"

        # Execute the update query with the provided values
        cursor.execute(query, list(updates.values()))

        conn.commit()

        print(f"Record(s) updated successfully in {table_name} where {condition}")

    except mysql.connector.Error as error:
        print(f"Failed to update data in MySQL table {table_name}: {error}")

    finally:
        close_connection(conn)

#4 Show DATA
def show_table(table_name,column):
    try:
        conn = create_connection()
        cursor = conn.cursor()

        query = f"SELECT {column} FROM {table_name}" 
        cursor.execute(query)
        
        # Fetch data and convert it into a DataFrame
        columns = showColumn(table_name)  # Get column names
        data = cursor.fetchall()
        
        if data:
            df = pd.DataFrame(data, columns=columns)
            return df  
        else:
            st.write("No data available.")
    except mysql.connector.Error as error:
        print(f"Failed to delete data from MySQL table {table_name}: {error}")
    finally:
        close_connection(conn)

def editable_dataframe(df):
    # Reset the index to ensure compatibility with grid data
    df = df.reset_index(drop=True)

    # Configure the editable table
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True)  # Enable editing for all columns

    # Columns that should not be editable
    not_edit = ["enrollment_id", "student_id", "course_id"]
    for col in not_edit:
        gb.configure_column(col, editable=False)

    grid_options = gb.build()

    # Display the editable table
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        height=300,
    )

    # Get the updated data from the grid
    updated_df = pd.DataFrame(grid_response['data']).reset_index(drop=True)

    if st.button("Save Changes"):
        # Identify rows with changes
        changed_rows = updated_df.compare(df, keep_shape=False).dropna()
        
        # Only update rows where there are actual changes
        if not changed_rows.empty:
            st.write(f"{len(changed_rows)} row(s) changed.")
            
            # Convert changed rows to a dictionary for efficient processing
            for index, changes in changed_rows.iterrows():
                # Original row data
                original_row = df.iloc[index]
                updated_row = updated_df.iloc[index]

                # Prepare SQL update query
                query = """
                UPDATE enrollment
                SET semester = %s, year = %s, grade = %s, enrollment_date = %s
                WHERE student_id = %s
                """
                params = (
                    updated_row["semester"],
                    updated_row["year"],
                    updated_row["grade"],
                    updated_row["enrollment_date"],
                    updated_row["student_id"],
                )

                # Execute the SQL update
                conn = create_connection()
                cursor = conn.cursor()

                cursor.execute(query, params)
                conn.commit()

                close_connection(conn)
                
                st.write(f"Updated record for student ID {updated_row['student_id']}.")
        else:
            st.write("No changes detected.")

    st.write("Updated Data:")
    st.dataframe(updated_df)

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
        st.title("SCENARY Backend.1")
        login()
    else:
        # Enable sidebar once logged in
        st.set_page_config(page_title="Main Page", layout="wide", initial_sidebar_state="expanded")

        # Once logged in, show the sidebar
        with st.sidebar:
            st.sidebar.title("University Enrollment Backend")
            menu = st.sidebar.selectbox("Menu", ["Dashboard", "Student Management", "Course Management", 
                                     "Enrollment Management", "Reports", "Settings"])

        if menu == "Dashboard":
            st.title("Dashboard Overview")
            st.metric("Total Enrollments", 1250)
            st.bar_chart(data={"Department A": 300, "Department B": 450, "Department C": 500})
        elif menu == "User Management":
            st.title("User Management")
            

        elif menu == "Student Management":
            st.title("Student Management")

        elif menu == "Course Management":
            st.title("Course Management")

        elif menu == "Enrollment Management":
            st.title("Enrollment Management")

            df= pd.DataFrame[
    {
        "enrollment_id": 1,
        "student_id": 101,
        "course_id": 201,
        "semester": "Fall",
        "year": 2023,
        "grade": "A",
        "enrollment_date": "2023-08-20"
    },
    {
        "enrollment_id": 2,
        "student_id": 102,
        "course_id": 202,
        "semester": "Spring",
        "year": 2024,
        "grade": "B",
        "enrollment_date": "2024-01-15"
    },
    {
        "enrollment_id": 3,
        "student_id": 103,
        "course_id": 203,
        "semester": "Summer",
        "year": 2023,
        "grade": "C",
        "enrollment_date": "2023-06-10"
    },
    {
        "enrollment_id": 4,
        "student_id": 104,
        "course_id": 204,
        "semester": "Fall",
        "year": 2023,
        "grade": None,
        "enrollment_date": "2023-09-01"
    },
    {
        "enrollment_id": 5,
        "student_id": 105,
        "course_id": 205,
        "semester": "Spring",
        "year": 2022,
        "grade": "A",
        "enrollment_date": "2022-02-20"
    },
    {
        "enrollment_id": 6,
        "student_id": 106,
        "course_id": 206,
        "semester": "Fall",
        "year": 2022,
        "grade": "B",
        "enrollment_date": "2022-09-12"
    },
    {
        "enrollment_id": 7,
        "student_id": 107,
        "course_id": 207,
        "semester": "Spring",
        "year": 2023,
        "grade": "D",
        "enrollment_date": "2023-03-22"
    },
    {
        "enrollment_id": 8,
        "student_id": 108,
        "course_id": 208,
        "semester": "Summer",
        "year": 2024,
        "grade": None,
        "enrollment_date": "2024-06-05"
    },
    {
        "enrollment_id": 9,
        "student_id": 109,
        "course_id": 209,
        "semester": "Fall",
        "year": 2024,
        "grade": "A",
        "enrollment_date": "2024-08-25"
    },
    {
        "enrollment_id": 10,
        "student_id": 110,
        "course_id": 210,
        "semester": "Spring",
        "year": 2022,
        "grade": "C",
        "enrollment_date": "2022-04-10"
    }
]

        editable_dataframe(df)

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