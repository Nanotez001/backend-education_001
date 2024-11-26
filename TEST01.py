def add_student_page():
    st.subheader("Add Student Data")
    # Add new student fields
    student_id = st.text_input('Student ID')
    first_name = st.text_input('First Name')
    last_name = st.text_input('Last Name')
    email = st.text_input('Email')
    contact_number = st.text_input('Contact Number')
    address = st.text_area('Address')

    if st.button('Add Student'):
        # Add student to the database
        register_date = today()

        # Add student to the database
        conn = create_connection()
        cursor = conn.cursor()

        query = '''
        INSERT INTO student (student_id, first_name, last_name, email, contact_number, address, register_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(query, (student_id, first_name, last_name, email, contact_number, address, register_date))
        conn.commit()
        close_connection(conn)

        st.success("New student added successfully!")