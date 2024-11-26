import streamlit as st
import mysql.connector
from mysql.connector import Error
from time import sleep
import hashlib
import pandas as pd
from streamlit_option_menu import option_menu
from datetime import datetime
import altair as alt
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

    cursor.execute("SELECT password_hash FROM admin WHERE username = %s ", (input_username,))
    result = cursor.fetchone()
    if result:
        stored_password = result[0]  # Get the stored password
        if hash_password(input_password) == stored_password:
        # if input_password == stored_password:
            st.session_state.logged_in = True  # Set login state to True
            st.success("Logged in!")
            # sleep(1)
            st.rerun()  # Rerun the app to show the sidebar
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

        # print(f"1 record inserted successfully into {table_name}")

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
def today():
    return datetime.today().strftime('%Y-%m-%d')

def login():
    input_username = st.text_input("Username", key="username")
    input_password = st.text_input("Password", key="password", type="password")
    if st.button("Login"):
        try_login(input_username, input_password)


# # ============================================


def dashboard_page():
    st.title("Dashboard Overview")

    # Create a connection to the database
    conn = create_connection()
    cursor = conn.cursor()

    # Query to count the total number of enrollments
    cursor.execute("SELECT COUNT(*) FROM enrollment")
    total_enrollments = cursor.fetchone()[0]

    # Query to count the total number of distinct students
    cursor.execute("SELECT COUNT(DISTINCT student_id) FROM student")
    total_students = cursor.fetchone()[0]

    # Query to count enrollments by course and fetch the course name
    cursor.execute("""
        SELECT c.course_name, COUNT(*) 
        FROM enrollment e
        JOIN course c ON e.course_id = c.course_id
        GROUP BY c.course_name
    """)
    course_counts = cursor.fetchall()

    # Prepare data for the chart
    course_data = {course[0]: course[1] for course in course_counts}
    course_df = pd.DataFrame(list(course_data.items()), columns=['Course Name', 'Enrollment Count'])

    # Close the connection
    close_connection(conn)

    # Display total students and total enrollments on the same row using columns
    col1, col2 = st.columns(2)  # Create two columns

    with col1:
        st.metric("Total Students", total_students)
    
    with col2:
        st.metric("Total Enrollments", total_enrollments)

    # Create a horizontal bar chart using Altair
    chart = alt.Chart(course_df).mark_bar().encode(
        x='Enrollment Count:Q',
        y='Course Name:N',
        color='Course Name:N'
    ).properties(
        title='Enrollments per Course',
        width=700,
        height=400
    )

    # Display the chart
    st.altair_chart(chart, use_container_width=True)



def student_management_page():
    st.title("Student Management")

    # Use st.tabs to create tabs
    tabs = st.tabs(["Edit Student Data", "Add Student Data", "Delete Student Data"])

    with tabs[0]:
        edit_student_page()

    with tabs[1]:
        add_student_page()

    with tabs[2]:
        delete_student_page()

def edit_student_page():
    st.subheader("Edit Student Data")
    df = show_table("student", "*")
    selected_row1 = st.selectbox('Select a Student ID', df['student_id'])

    selected_data = df[df['student_id'] == selected_row1].iloc[0]

    # Edit values with inputs
    first_name_edit = st.text_input('First Name', selected_data['first_name'])
    last_name_edit = st.text_input('Last Name', selected_data['last_name'])
    email_edit = st.text_input('Email', selected_data['email'])
    contact_number_edit = st.text_input('Contact Number', selected_data['contact_number'])
    address_edit = st.text_area('Address', selected_data['address'])

    if st.button('Save Changes'):
        conn = create_connection()
        cursor = conn.cursor()

        query = '''
        UPDATE student
        SET first_name = %s, last_name = %s, email = %s, contact_number = %s, address = %s
        WHERE student_id = %s
        '''
        cursor.execute(query, (first_name_edit, last_name_edit, email_edit, contact_number_edit, address_edit, selected_row1))
        conn.commit()
        close_connection(conn)

        st.success("Student details updated successfully!")
        # Reload updated data
        df = show_table("student", "*")
    df["student_id"] = df["student_id"].astype(str)
    st.dataframe(df)

import pandas as pd

def add_student_page():
    st.subheader("Add Student Data")
    
    # Option to add students manually or via CSV
    add_option = st.radio("Add Students", options=["Manually", "Upload CSV"], index=0)
    
    if add_option == "Manually":
        # Add new student fields
        student_id = st.text_input('Student ID')
        first_name = st.text_input('First Name')
        last_name = st.text_input('Last Name')
        email = st.text_input('Email')
        contact_number = st.text_input('Contact Number')
        address = st.text_area('Address')

        if st.button('Add Student'):
            # Get the current date
            register_date = today() 
            created_at = today() 

            conn = create_connection()
            cursor = conn.cursor()

            query = '''
            INSERT INTO student (student_id, first_name, last_name, email, contact_number, address, register_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(query, (student_id, first_name, last_name, email, contact_number, address, register_date))

            login_query = '''
            INSERT INTO student_login (student_id,password,created_at)
            VALUES (%s, %s, %s)
            '''
            cursor.execute(login_query, (student_id, student_id,created_at))
            
            conn.commit()
            close_connection(conn)

            st.success("New student added successfully!")
    
    elif add_option == "Upload CSV":
        # File uploader for CSV
        uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
        
        if uploaded_file:
            # Read the uploaded CSV file
            csv_data = pd.read_csv(uploaded_file)
            
            # Display the CSV data for confirmation
            st.write("Preview of uploaded data:")
            st.dataframe(csv_data)

            # Check if required columns exist
            required_columns = ['student_id', 'first_name', 'last_name', 'email', 'contact_number', 'address']
            if all(col in csv_data.columns for col in required_columns):
                if st.button('Add Students from CSV'):
                    # Add students to the database
                    conn = create_connection()
                    cursor = conn.cursor()
                    register_date = today()
                    
                    for _, row in csv_data.iterrows():
                        query = '''
                        INSERT INTO student (student_id, first_name, last_name, email, contact_number, address, register_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        '''
                        cursor.execute(query, (
                            row['student_id'], row['first_name'], row['last_name'], 
                            row['email'], row['contact_number'], row['address'], register_date
                        ))
                    
                    conn.commit()
                    close_connection(conn)

                    st.success("All students from the CSV file have been added successfully!")
            else:
                st.error(f"CSV file must include the following columns: {', '.join(required_columns)}")


def delete_student_page():
    st.subheader("Delete Student Data")

    # Fetch the student data from the database
    df = show_table("student", "*")

    # Create a selectbox to choose a student ID
    selected_row1 = st.selectbox('Select a Student ID to Delete', df['student_id'])

    # Get the selected student's data
    selected_data = df[df['student_id'] == selected_row1].iloc[0]  # Fetch the row data

    # Display the details of the selected student
    st.dataframe(selected_data)

    # Ask for confirmation before deletion
    confirm_delete = st.button('Confirm Deletion')

    if confirm_delete:
        # Proceed with deletion if confirmed
        conn = create_connection()
        cursor = conn.cursor()

        # Delete dependent rows in the student_login table
        delete_login_query = '''
        DELETE FROM student_login WHERE student_id = %s
        '''
        cursor.execute(delete_login_query, (selected_row1,))

        # Now delete the student record
        delete_student_query = '''
        DELETE FROM student WHERE student_id = %s
        '''
        cursor.execute(delete_student_query, (selected_row1,))

        conn.commit()
        close_connection(conn)

        st.success(f"Student with ID {selected_row1} and their login data deleted successfully!")

# ===================================================

def course_management_page():
    st.title("Course Management")

    # Use st.tabs to create tabs for Edit, Add, and Delete operations
    tabs = st.tabs(["Edit Course Data", "Add Course Data", "Delete Course Data"])

    with tabs[0]:
        edit_course_page()

    with tabs[1]:
        add_course_page()

    with tabs[2]:
        delete_course_page()

# Edit Course Page
def edit_course_page():
    st.subheader("Edit Course Data")
    
    # Fetch data for courses, departments, and instructors
    course_df = show_table("course", "*")  # Fetch course data from the database
    department_df = show_table("department", "*")  # Fetch department data
    instructor_df = show_table("instructor", "*")  # Fetch instructor data

    # Create descriptive labels for courses
    course_options = course_df.apply(
        lambda row: f"{row['course_id']}-{row['course_name']}", axis=1
    )
    course_mapping = {f"{row['course_id']}-{row['course_name']}": row['course_id'] for _, row in course_df.iterrows()}

    # Create descriptive labels for departments and instructors
    department_options = department_df.apply(
        lambda row: f"{row['department_id']}-{row['department_name']}", axis=1
    )
    instructor_options = instructor_df.apply(
        lambda row: f"{row['instructor_id']}-{row['first_name']} {row['last_name']}", axis=1
    )

    # Map descriptive labels to their actual IDs for processing
    department_mapping = {f"{row['department_id']}-{row['department_name']}": row['department_id'] for _, row in department_df.iterrows()}
    instructor_mapping = {f"{row['instructor_id']}-{row['first_name']} {row['last_name']}": row['instructor_id'] for _, row in instructor_df.iterrows()}

    # Select a course by descriptive label
    selected_course_label = st.selectbox('Select a Course', course_options)
    selected_course = course_mapping[selected_course_label]
    selected_data = course_df[course_df['course_id'] == selected_course].iloc[0]

    # Edit values with inputs
    course_name_edit = st.text_input('Course Name', selected_data['course_name'])
    credits_edit = st.number_input('Credits', value=selected_data['credits'], step=1)

    # Select department using descriptive labels
    current_department_label = f"{selected_data['department_id']}-{department_df[department_df['department_id'] == selected_data['department_id']]['department_name'].values[0]}"
    department_id_label_edit = st.selectbox(
        'Department', department_options, index=department_options.tolist().index(current_department_label)
    )
    department_id_edit = department_mapping[department_id_label_edit]  # Get the actual department ID

    # Select instructor using descriptive labels
    current_instructor_label = f"{selected_data['instructor_id']}-{instructor_df[instructor_df['instructor_id'] == selected_data['instructor_id']]['first_name'].values[0]} {instructor_df[instructor_df['instructor_id'] == selected_data['instructor_id']]['last_name'].values[0]}"
    instructor_id_label_edit = st.selectbox(
        'Instructor', instructor_options, index=instructor_options.tolist().index(current_instructor_label)
    )
    instructor_id_edit = instructor_mapping[instructor_id_label_edit]  # Get the actual instructor ID

    # Save changes to the database
    if st.button('Save Changes'):
        conn = create_connection()
        cursor = conn.cursor()

        query = '''
        UPDATE course
        SET course_name = %s, credits = %s, department_id = %s, instructor_id = %s
        WHERE course_id = %s
        '''
        cursor.execute(
            query,
            (course_name_edit, credits_edit, department_id_edit, instructor_id_edit, selected_course)
        )
        conn.commit()
        close_connection(conn)

        st.success("Course details updated successfully!")

        # Reload updated data
        course_df = show_table("course", "*")
    
    # Display the updated course table
    course_df["course_id"] = course_df["course_id"].astype(str)
    course_df["instructor_id"] = course_df["instructor_id"].astype(str)
    st.dataframe(course_df)


# Add Course Page
def add_course_page():
    st.subheader("Add Course")
    
    # Fetch existing department_ids and department_names from the database
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT department_id, department_name FROM department") 
    departments = cursor.fetchall()  # Get both department_id and department_name
    department_dict = {dept[0]: dept[1] for dept in departments}  # Create a dictionary for easy access
    department_ids = list(department_dict.keys())  # Get the list of department_ids

    cursor.execute("SELECT instructor_id, first_name,last_name FROM instructor") 
    instructors = cursor.fetchall()  # Get both instructor_id and instructor_name
    instructor_dict = {instructor[0]: f"{instructor[1]} {instructor[2]}" for instructor in instructors}  # Combine first_name and last_name
    instructor_ids = list(instructor_dict.keys())  # Get the list of instructor_ids

    close_connection(conn)

    # Other course details
    course_id = st.text_input('Course ID')
    course_name = st.text_input('Course Name')
    credits = st.number_input('Credits', min_value=1, max_value=4, step=1)

    # Select Department with names
    department_id = st.selectbox(
        'Select Department',
        department_ids,
        format_func=lambda x: f"{department_dict[x]}"  # Show department_name instead of department_id
    )
    
    # Select Instructor with names
    instructor_id = st.selectbox(
        'Select Instructor',
        instructor_ids,
        format_func=lambda x: f"{instructor_dict[x]}"  # Show instructor_name instead of instructor_id
    )

    if st.button('Add Course'):
        # Add course to the database
        insert_data_course(course_id, course_name, credits, department_id, instructor_id)

        st.success("New course added successfully!")

# Delete Course Page
def delete_course_page():
    st.subheader("Delete Course")

    # Fetch course data from the database
    df = show_table("course", "*")

    # Create a selectbox to choose a course ID
    selected_row1 = st.selectbox('Select a Course ID to Delete', df['course_id'])

    # Get the selected course's data
    selected_data = df[df['course_id'] == selected_row1].iloc[0]  # Fetch the row data

    st.dataframe(selected_data)

    # Ask for confirmation before deletion
    confirm_delete = st.button('Confirm Deletion')

    if confirm_delete:
        # Proceed with deletion if confirmed
        conn = create_connection()
        cursor = conn.cursor()

        query = '''
        DELETE FROM course WHERE course_id = %s
        '''
        cursor.execute(query, (selected_row1,))
        conn.commit()
        close_connection(conn)

        st.success(f"Course with ID {selected_row1} deleted successfully!")

#========================================
# Enrollment Management Page
def enrollment_management_page():
    st.title("Enrollment Management")

    # Use st.tabs to create tabs for Edit, Add, and Delete operations
    tabs = st.tabs(["Edit Enrollment", "Add Enrollment", "Delete Enrollment"])

    with tabs[0]:
        edit_enrollment_page()

    with tabs[1]:
        add_enrollment_page()

    with tabs[2]:
        delete_enrollment_page()

# Edit Enrollment Page
def edit_enrollment_page():
    st.subheader("Edit Enrollment Data")
    df = show_table("enrollment", "*")  # Fetch enrollment data from the database
    selected_row1 = st.selectbox('Select Enrollment ID', df['enrollment_id'])

    selected_data = df[df['enrollment_id'] == selected_row1].iloc[0]

    # Edit values with inputs
    st.write('Student ID', selected_data['student_id'])
    st.write('Course ID', selected_data['course_id'])
    
    semester_edit = st.number_input(
    label='Semester',value=int(selected_data['semester']), min_value=1,max_value=3,step=1)
    year_edit = st.number_input('Year',value=int(selected_data['year']), min_value=2000, max_value=2100, step=1)
    grade_options = ["A", "B+", "B", "C+", "C", "D+", "D", "F", "W", "O", "S", "U"]  
    grade_edit = st.selectbox('Select Grade',options=grade_options,
    index=grade_options.index(selected_data['grade']) if selected_data['grade'] in grade_options else 0)

    enrollment_date_edit = today()

    if st.button('Save Changes'):
        conn = create_connection()
        cursor = conn.cursor()

        query = '''
        UPDATE enrollment
        SET semester = %s, year = %s, grade = %s, enrollment_date = %s
        WHERE enrollment_id = %s
        '''
        cursor.execute(query, (semester_edit, year_edit, grade_edit, enrollment_date_edit, selected_row1))
        conn.commit()
        close_connection(conn)

        st.success("Enrollment details updated successfully!")

        # Reload updated data
        df = show_table("enrollment", "*")
    df["course_id"] = df["course_id"].astype(str)
    df["student_id"] = df["student_id"].astype(str)
    df["year"] = df["year"].astype(str)
    st.dataframe(df)

# Add Enrollment Page
def add_enrollment_page():
    st.subheader("Add Enrollment")
    
    # Fetch existing student_ids and course_ids from the database
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT student_id FROM student")
    student_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT course_id, course_name FROM course")
    courses = cursor.fetchall()  # Get both course_id and course_name
    course_dict = {course[0]: course[1] for course in courses}  # Create a dictionary for easy access
    course_ids = list(course_dict.keys())  # Get the list of course_ids

    close_connection(conn)

    # Other enrollment details
    enrollment_id = st.text_input('Enrollment ID')
    student_id = st.selectbox('Select Student', student_ids)
    
    # Show course ID and name in the format "Course ID - Course Name"
    course_id = st.selectbox(
        'Select Course',
        course_ids,
        format_func=lambda x: f"{x} - {course_dict[x]}"  # Format as "Course ID - Course Name"
    )
    
    semester = st.number_input('Semester', min_value=1, max_value=3, step=1, key="semester_input")
    year = st.number_input('Year', min_value=2000, max_value=2100, step=1, key="year_input")
    
    # grade_options = ["A", "B+", "B", "C+", "C", "D+", "D", "F", "W", "O", "S", "U"]  # List of possible grades
    # grade = st.selectbox('Select Grade', grade_options)
    
    enrollment_date = today() 

    if st.button('Add Enrollment'):
        # Add enrollment to the database
        insert_data_enrollment(enrollment_id, student_id, course_id, semester, year, grade, enrollment_date)

        st.success("New enrollment added successfully!")



# Delete Enrollment Page
def delete_enrollment_page():
    st.subheader("Delete Enrollment")

    # Fetch enrollment data from the database
    df = show_table("enrollment", "*")

    # Create a selectbox to choose an enrollment ID
    selected_row1 = st.selectbox('Select an Enrollment ID to Delete', df['enrollment_id'])

    # Get the selected enrollment's data
    selected_data = df[df['enrollment_id'] == selected_row1].iloc[0]  # Fetch the row data

    st.dataframe(selected_data)

    # Ask for confirmation before deletion
    confirm_delete = st.button('Confirm Deletion')

    if confirm_delete:
        # Proceed with deletion if confirmed
        conn = create_connection()
        cursor = conn.cursor()

        query = '''
        DELETE FROM enrollment WHERE enrollment_id = %s
        '''
        cursor.execute(query, (selected_row1,))
        conn.commit()
        close_connection(conn)

        st.success(f"Enrollment with ID {selected_row1} deleted successfully!")
# ====================================
def instructor_management_page():
    st.title("Instructor Management")

    # Use st.tabs to create tabs
    tabs = st.tabs(["Edit Instructor Data", "Add Instructor Data", "Delete Instructor Data"])

    with tabs[0]:
        edit_instructor_page()

    with tabs[1]:
        add_instructor_page()

    with tabs[2]:
        delete_instructor_page()


def edit_instructor_page():
    st.subheader("Edit Instructor Data")
    
    # Fetch data for instructors and departments
    instructor_df = show_table("instructor", "*")  # Fetch data from the instructor table
    department_df = show_table("department", "*")  # Fetch data from the department table

    # Create descriptive labels for instructors and departments
    instructor_options = instructor_df.apply(
        lambda row: f"{row['instructor_id']}-{row['first_name']} {row['last_name']}", axis=1
    )
    department_options = department_df.apply(
        lambda row: f"{row['department_id']}-{row['department_name']}", axis=1
    )

    # Map descriptive labels to their actual IDs for processing
    instructor_mapping = {f"{row['instructor_id']}-{row['first_name']} {row['last_name']}": row['instructor_id'] for _, row in instructor_df.iterrows()}
    department_mapping = {f"{row['department_id']}-{row['department_name']}": row['department_id'] for _, row in department_df.iterrows()}

    # Select an instructor by ID
    selected_instructor_label = st.selectbox('Select an Instructor', instructor_options)
    selected_instructor = instructor_mapping[selected_instructor_label]  # Get the actual instructor ID

    # Get the selected instructor's data
    selected_data = instructor_df[instructor_df['instructor_id'] == selected_instructor].iloc[0]

    # Populate fields with current data
    first_name_edit = st.text_input('First Name', selected_data['first_name'])
    last_name_edit = st.text_input('Last Name', selected_data['last_name'])

    # Select department using descriptive labels
    current_department_label = f"{selected_data['department_id']}-{department_df[department_df['department_id'] == selected_data['department_id']]['department_name'].values[0]}"
    department_id_label_edit = st.selectbox(
        'Department', department_options, index=department_options.tolist().index(current_department_label)
    )
    department_id_edit = department_mapping[department_id_label_edit]  # Get the actual department ID

    email_edit = st.text_input('Email', selected_data['email'])
    contact_number_edit = st.text_input('Contact Number', selected_data['contact_number'])

    # Save changes to the database
    if st.button('Save Changes'):
        conn = create_connection()
        cursor = conn.cursor()

        query = '''
        UPDATE instructor
        SET first_name = %s, last_name = %s, department_id = %s, email = %s, contact_number = %s
        WHERE instructor_id = %s
        '''
        cursor.execute(
            query,
            (first_name_edit, last_name_edit, department_id_edit, email_edit, contact_number_edit, selected_instructor)
        )
        conn.commit()
        close_connection(conn)

        st.success("Instructor details updated successfully!")

        # Reload updated data
        instructor_df = show_table("instructor", "*")

    # Display the updated instructor table
    st.dataframe(instructor_df)


def add_instructor_page():
    st.subheader("Add Instructor Data")

    # Fetch department data from the department table
    department_df = show_table("department", "department_id, department_name")  # Assuming this fetches department_id and department_name

    # Combine department_id and department_name for display in the selectbox
    department_options = department_df.apply(lambda x: f"{x['department_id']}-{x['department_name']}", axis=1).tolist()

    # Add new instructor fields
    instructor_id = st.text_input('Instructor ID')
    first_name = st.text_input('First Name')
    last_name = st.text_input('Last Name')
    selected_department = st.selectbox('Select Department', department_options)
    email = st.text_input('Email')
    contact_number = st.text_input('Contact Number')

    # Extract department_id from the selected value
    department_id = selected_department.split('-')[0]

    if st.button('Add Instructor'):
        conn = create_connection()
        cursor = conn.cursor()

        query = '''
        INSERT INTO instructor (instructor_id, first_name, last_name, department_id, email, contact_number)
        VALUES (%s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(query, (instructor_id, first_name, last_name, department_id, email, contact_number))
        conn.commit()
        close_connection(conn)

        st.success(f"New instructor with ID {instructor_id} added successfully!")


def delete_instructor_page():
    st.subheader("Delete Instructor Data")

    # Fetch the instructor data from the database
    df = show_table("instructor", "*")

    # Create a selectbox to choose an instructor ID
    selected_instructor = st.selectbox('Select an Instructor ID to Delete', df['instructor_id'])

    # Get the selected instructor's data
    selected_data = df[df['instructor_id'] == selected_instructor].iloc[0]  # Fetch the row data

    # Display the details of the selected instructor
    st.dataframe(selected_data)

    # Ask for confirmation before deletion
    confirm_delete = st.button('Confirm Deletion')

    if confirm_delete:
        # Proceed with deletion if confirmed
        conn = create_connection()
        cursor = conn.cursor()

        delete_query = '''
        DELETE FROM instructor WHERE instructor_id = %s
        '''
        cursor.execute(delete_query, (selected_instructor,))
        conn.commit()
        close_connection(conn)

        st.success(f"Instructor with ID {selected_instructor} deleted successfully!")

# ====================================
def report_page():
    st.title("University Report Page")

    # Grade Distribution Report
    st.header("Grade Distribution Report")

    # Query to get all course names for the selectbox
    conn = create_connection()
    cursor = conn.cursor()

    # Fetch course names
    cursor.execute("SELECT DISTINCT course_name FROM course")
    courses = [row[0] for row in cursor.fetchall()]

    # Select course from the list
    selected_course = st.selectbox("Select a Course", options=courses)

    # Query to get grade distribution for the selected course
    query = """
        SELECT grade, COUNT(*) as grade_count
        FROM enrollment e
        JOIN course c ON e.course_id = c.course_id
        WHERE c.course_name = %s
        GROUP BY grade
    """
    cursor.execute(query, (selected_course,))
    grade_data = cursor.fetchall()

    close_connection(conn)

    # Convert data to DataFrame
    grade_df = pd.DataFrame(grade_data, columns=["Grade", "Count"])

    # Display grade distribution bar chart
    if not grade_df.empty:
        grade_chart = alt.Chart(grade_df).mark_bar().encode(
            x=alt.X('Count:Q', axis=alt.Axis(format="d"), title="Count"),
            y=alt.Y('Grade:N', title="Grade"),
            color='Grade:N'
        ).properties(
            title=f"Grade Distribution for {selected_course}",
            width=600,
            height=400
        )
        st.altair_chart(grade_chart, use_container_width=True)
    else:
        st.warning("No grade data available for the selected course.")

        # Grade distribution pie chart (for overall grades)
        overall_grade_data = grade_df.groupby('Grade')['Count'].sum().reset_index()
        overall_grade_chart = alt.Chart(overall_grade_data).mark_arc().encode(
        theta='Count:Q',
        color='Grade:N',
        tooltip=['Grade:N', 'Count:Q']
        ).properties(
        title="Overall Grade Distribution",
        width=400,
        height=400
        )
        st.altair_chart(overall_grade_chart, use_container_width=True)


    # Course Performance Summary
    st.header("Course Performance Summary")

    # Query to get the number of students per course and average grade
    conn = create_connection()
    query = """
        SELECT course_name, COUNT(*) as student_count, AVG(CASE
            WHEN grade = 'A' THEN 4
            WHEN grade = 'B+' THEN 3.5
            WHEN grade = 'B' THEN 3
            WHEN grade = 'C+' THEN 2.5
            WHEN grade = 'C' THEN 2
            WHEN grade = 'D+' THEN 1.5
            WHEN grade = 'D' THEN 1
            WHEN grade = 'F' THEN 0
            ELSE NULL END) as average_grade
        FROM enrollment e
        JOIN course c ON e.course_id = c.course_id
        GROUP BY course_name
    """
    cursor = conn.cursor()
    cursor.execute(query)
    course_performance_data = cursor.fetchall()
    close_connection(conn)

    performance_df = pd.DataFrame(course_performance_data, columns=["Course Name", "Student Count", "Average Grade"])

    # Display course performance summary
    st.dataframe(performance_df)

    # Visualization: Number of Students per Course
    student_count_chart = alt.Chart(performance_df).mark_bar().encode(
        y='Course Name:N',
        x=alt.X('Student Count:Q',axis=alt.Axis(format="d")),
        color='Course Name:N'
    ).properties(title="Number of Students per Course", width=700, height=400)
    st.altair_chart(student_count_chart)


    performance_df['Average Grade'] = performance_df['Average Grade'].astype(float)
    # Visualization: Average Grade per Course (on a 4-point scale)
    avg_grade_chart = alt.Chart(performance_df).mark_bar().encode(
        y='Course Name:N',
        x=alt.X('Average Grade:Q', title='Average Grade', axis=alt.Axis(format=".2f")), 
        color='Course Name:N'
    ).properties(title="Average Grade per Course", width=700, height=400)
    st.altair_chart(avg_grade_chart)



# ===========================================================
# SETTING
def setting_page():
    st.header("Settings")

    # Add your settings options here
    st.subheader("Manage your preferences")
    
    toggle = st.radio("Enrollment Setting", options=["ON","OFF"], index=0)

    

    if toggle == "ON":
        st.write("Enrollment ENABLE")
        # st.session_state['Enrollment state'] = "ENABLE"

    elif toggle == "OFF":
        st.write("Enrollment UNABLE")
        # st.session_state['Enrollment state'] = "UNABLE"

    # elif toggle == "TIME SET":
    # # Get the current date and time
    # current_datetime = datetime.now()
    #     # Allow the user to set an end date and time
    #     end_date = st.date_input("OFF AT")
    #     end_time = st.time_input("Time")

    #     # Combine the date and time selected by the user into a datetime object
    #     end_datetime = datetime.combine(end_date, end_time)

    #     # Show the end date and time
    #     st.write(f"Enrollment will end at: {end_datetime}")
        
    #     # Check if the current date and time is past the end time
    #     if current_datetime > end_datetime:
    #         st.write("Enrollment UNABLE")
    #         st.session_state['Enrollment state'] = "UNABLE"
    #     else:
    #         remaining_time = end_datetime - current_datetime
    #         st.write(f"Enrollment is still OPEN. Time remaining: {remaining_time}")
    #         st.session_state['Enrollment state'] = "ENABLE"
        



    # Add a Logout button in the settings page
    if st.button('Logout'):
        # Clear session state and redirect to login page
        st.session_state.clear()
        st.session_state['current_page'] = "Login"
        st.rerun()
    
#========================================
# Main
def main():
    # Initialize session state for login status if not already initialized
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False  # Default to False if not logged in

    # Disable sidebar during the login process
    if not st.session_state.logged_in:
        st.set_page_config(page_title="Login", layout="centered", initial_sidebar_state="collapsed")
        st.title("SCENARY Backend v.5.82")
        login()
    else:
        # Enable sidebar once logged in
        st.set_page_config(page_title="Main Page", layout="wide", initial_sidebar_state="expanded")

        # Once logged in, show the sidebar
        # with st.sidebar:
        #     st.sidebar.title("University Enrollment Backend")
            # menu = st.sidebar.selectbox("Menu", ["Dashboard", "Student Management", "Course Management", 
            #                          "Enrollment Management", "Reports", "Settings"])


        with st.sidebar:
            selected_option = option_menu(
                menu_title="Navigation",
                options=["Dashboard", "Student Management", "Enrollment Management", "Course Management", 
                         "Instructor Management", "Reports", "Settings"],
                icons=["house", "person", "clipboard-check", "book", "person", "bar-chart", "gear"],
                menu_icon="cast",
                default_index=0,
                )

            if selected_option == "Logout":
                st.session_state.clear()
                st.session_state['current_page'] = "Login"
                st.rerun()
            else:
                st.session_state['current_page'] = selected_option

        # Render the selected page
        if st.session_state["current_page"] == "Dashboard":
            dashboard_page()
        elif st.session_state["current_page"] == "Student Management":
            student_management_page()
        elif st.session_state["current_page"] == "Course Management":
            course_management_page()
        elif st.session_state["current_page"] == "Enrollment Management":
            enrollment_management_page()
        elif st.session_state["current_page"] == "Instructor Management":
            instructor_management_page()
        elif st.session_state["current_page"] == "Reports":
            report_page()
        elif st.session_state["current_page"] == "Settings":
            setting_page()
        
            
# ==========================

# Run the app
if __name__ == "__main__":
    main()

#========================================
# Test Database Connection
# st.write("TEST Connection") 
# conn = create_connection()
# if conn:
#     st.write("Connected to MySQL database")
#     cursor = conn.cursor()
# else:
#     st.error("Failed to connect to the database.")
# st.write("Session State:", st.session_state)
# close_connection(conn)