Diagram
    STUDENTS {
        int student_id PK
        string student_number UK
        string first_name
        string last_name
        string email UK
        string phone
        date date_of_birth
        string address
        string gender
        date enrollment_date
        string status
        int program_id FK
        datetime created_at
        datetime updated_at
    }

    PROGRAMS {
        int program_id PK
        string program_code UK
        string program_name
        string degree_level
        int duration_years
        int department_id FK
        decimal fees_per_semester
        string status
    }

    DEPARTMENTS {
        int department_id PK
        string department_code UK
        string department_name
        int faculty_id FK
        int head_of_department_id FK
    }

    FACULTIES {
        int faculty_id PK
        string faculty_code UK
        string faculty_name
        int dean_id FK
    }

    COURSES {
        int course_id PK
        string course_code UK
        string course_name
        int credit_hours
        string description
        int department_id FK
        string semester
        string level
    }

    ENROLLMENTS {
        int enrollment_id PK
        int student_id FK
        int course_id FK
        int lecturer_id FK
        string academic_year
        string semester
        datetime enrollment_date
        string status
    }

    GRADES {
        int grade_id PK
        int enrollment_id FK
        decimal assignment_marks
        decimal exam_marks
        decimal total_marks
        string letter_grade
        decimal gpa_points
        date grade_date
        int graded_by FK
    }

    STAFF {
        int staff_id PK
        string staff_number UK
        string first_name
        string last_name
        string email UK
        string phone
        string position
        int department_id FK
        decimal salary
        date hire_date
        string status
        string role
    }

    TIMETABLES {
        int timetable_id PK
        int course_id FK
        int lecturer_id FK
        string room_number
        string day_of_week
        time start_time
        time end_time
        string academic_year
        string semester
    }

    FEES {
        int fee_id PK
        int student_id FK
        string fee_type
        decimal amount
        date due_date
        string status
        string academic_year
        string semester
    }

    PAYMENTS {
        int payment_id PK
        int fee_id FK
        decimal amount_paid
        date payment_date
        string payment_method
        string reference_number
        string status
    }

    LIBRARY_BOOKS {
        int book_id PK
        string isbn UK
        string title
        string author
        string publisher
        int quantity_total
        int quantity_available
        string category
        decimal fine_per_day
    }

    LIBRARY_LOANS {
        int loan_id PK
        int student_id FK
        int book_id FK
        date loan_date
        date due_date
        date return_date
        decimal fine_amount
        string status
    }

    ACCOMMODATIONS {
        int room_id PK
        string room_number UK
        string building
        string room_type
        int capacity
        decimal fee_per_semester
        string status
    }

    ROOM_ALLOCATIONS {
        int allocation_id PK
        int student_id FK
        int room_id FK
        date allocation_date
        date move_out_date
        string academic_year
        string status
    }

    %% Relationships
    STUDENTS ||--o{ ENROLLMENTS : enrolls
    COURSES ||--o{ ENROLLMENTS : "has enrolled students"
    STAFF ||--o{ ENROLLMENTS : teaches
    ENROLLMENTS ||--|| GRADES : "receives grade"
    
    STUDENTS }|--|| PROGRAMS : "studies in"
    PROGRAMS }|--|| DEPARTMENTS : "belongs to"
    DEPARTMENTS }|--|| FACULTIES : "part of"
    COURSES }|--|| DEPARTMENTS : "offered by"
    
    STAFF }|--|| DEPARTMENTS : "works in"
    DEPARTMENTS ||--o| STAFF : "headed by"
    FACULTIES ||--o| STAFF : "led by dean"
    
    COURSES ||--o{ TIMETABLES : "scheduled in"
    STAFF ||--o{ TIMETABLES : "teaches at"
    
    STUDENTS ||--o{ FEES : "owes"
    FEES ||--o{ PAYMENTS : "paid through"
    
    STUDENTS ||--o{ LIBRARY_LOANS : "borrows"
    LIBRARY_BOOKS ||--o{ LIBRARY_LOANS : "loaned as"
    
    STUDENTS ||--o{ ROOM_ALLOCATIONS : "allocated to"
    ACCOMMODATIONS ||--o{ ROOM_ALLOCATIONS : "houses"
    
    STAFF ||--o{ GRADES : "assigns grade"
