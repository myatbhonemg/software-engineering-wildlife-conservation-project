--During the process of creating School / community admin 
--account Admin provides School / Community details
--and it will be stored in the below table
CREATE TABLE IF NOT EXISTS organization(
    organization_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT CHECK(category IN ('school', 'community')) NOT NULL,
    type  TEXT,
    email  VARCHAR(50) NOT NULL,
    address  TEXT,
    avatar TEXT
);


--When user inputs his email and password it chekcs the users 
--table to authenticate the user
CREATE TABLE IF NOT EXISTS user(
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT,
    password TEXT NOT NULL,
    organization_id INTEGER,
    avatar TEXT,
    phone TEXT,
    location TEXT,
    FOREIGN KEY (organization_id) REFERENCES organization(organization_id)
    created_at TIMESTAMP DEFAULT '2025-01-01',
    status TEXT DEFAULT 'active',
    points INTEGER DEFAULT 0
);

--Registration table for student and teacher registrations in school
CREATE TABLE IF NOT EXISTS registration (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student',
    access_code TEXT UNIQUE,
    organization_id INTEGER REFERENCES organization(organization_id),
    status TEXT CHECK(status IN ('pending', 'registered')) DEFAULT 'pending',
    created_at TEXT DEFAULT (datetime('now'))
);

--All the data about species
CREATE TABLE IF NOT EXISTS species (
    species_id INTEGER PRIMARY KEY AUTOINCREMENT,
    common_name TEXT NOT NULL,
    scientific_name TEXT NOT NULL,
    status TEXT CHECK(status IN ('CR', 'EN', 'VU')) NOT NULL,
    description TEXT,
    image TEXT,
    diet TEXT CHECK(diet IN ('Herbivore', 'Carnivore', 'Omnivore')),
    location TEXT,
    fun_fact TEXT,
    category TEXT,
    full_details_url TEXT
);

-- Sightings Table
CREATE TABLE IF NOT EXISTS sighting (
    sighting_id INTEGER PRIMARY KEY AUTOINCREMENT,
    species_id INTEGER NOT NULL,
    count INTEGER NOT NULL DEFAULT 1,
    location TEXT NOT NULL,
    region TEXT NOT NULL,
    sighting_date DATE NOT NULL,
    sighting_time TIME,
    description TEXT NOT NULL,
    condition TEXT,
    photo TEXT,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (species_id) REFERENCES species(species_id),
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

--Email table takes senders id and receiver id as foreign key text message
CREATE TABLE "message" (
	"message_id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"subject"	TEXT,
	"body"	TEXT NOT NULL,
	"sent_at"	DATETIME DEFAULT CURRENT_TIMESTAMP,
	"is_read"	INTEGER DEFAULT 0,
	"sender_id"	INTEGER NOT NULL,
	"receiver_id"	INTEGER NOT NULL,
	"attachment"	TEXT,
	FOREIGN KEY("receiver_id") REFERENCES "user"("user_id"),
	FOREIGN KEY("sender_id") REFERENCES "user"("user_id")
);

--Program details will be stored in programs table
CREATE TABLE IF NOT EXISTS program (
    program_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    species_focus TEXT,
    duration TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    FOREIGN KEY (created_by) REFERENCES user(user_id),
    FOREIGN KEY (organization_id) REFERENCES organization(organization_id)
);

--Files from programs will be stored in a seperate table
CREATE TABLE IF NOT EXISTS program_file (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (program_id) REFERENCES program(program_id)
);

-- Enrollment details table
CREATE TABLE IF NOT EXISTS enrollment (
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    program_id INTEGER NOT NULL,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT DEFAULT 'enrolled',
    FOREIGN KEY (student_id) REFERENCES user(user_id),
    FOREIGN KEY (program_id) REFERENCES program(program_id),
    UNIQUE(student_id, program_id)
);

-- To store student progress on programs
CREATE TABLE IF NOT EXISTS file_progress (
    progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    file_id INTEGER NOT NULL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES user(user_id),
    FOREIGN KEY (file_id) REFERENCES program_file(file_id),
    UNIQUE(student_id, file_id)
);

-- Challenge table to stor challenges data
CREATE TABLE IF NOT EXISTS challenge (
    challenge_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    points INTEGER NOT NULL DEFAULT 10,
    duration_days INTEGER NOT NULL DEFAULT 7,
    deadline TIMESTAMP NOT NULL,
    species_focus TEXT,
    created_by INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES user(user_id),
    FOREIGN KEY (organization_id) REFERENCES organization(organization_id)
);

-- To store the submision details for challenges
CREATE TABLE IF NOT EXISTS challenge_submission (
    submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    challenge_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    media_path TEXT,
    description TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'completed',
    FOREIGN KEY (challenge_id) REFERENCES challenge(challenge_id),
    FOREIGN KEY (student_id) REFERENCES user(user_id),
    UNIQUE(challenge_id, student_id)
);

-- Class table
CREATE TABLE IF NOT EXISTS class (
    class_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    subject TEXT,
    organization_id INTEGER NOT NULL,
    teacher_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organization(organization_id),
    FOREIGN KEY (teacher_id) REFERENCES user(user_id)
);

-- Class Enrollment table
CREATE TABLE IF NOT EXISTS class_enrollment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES class(class_id),
    FOREIGN KEY (student_id) REFERENCES user(user_id),
    UNIQUE(class_id, student_id)
);

-- programs in the class
CREATE TABLE IF NOT EXISTS program_class (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (program_id) REFERENCES program(program_id),
    FOREIGN KEY (class_id) REFERENCES class(class_id),
    UNIQUE(program_id, class_id)
);

-- challenges in the class
CREATE TABLE IF NOT EXISTS challenge_class (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    challenge_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (challenge_id) REFERENCES challenge(challenge_id),
    FOREIGN KEY (class_id) REFERENCES class(class_id),
    UNIQUE(challenge_id, class_id)
);

/*
--Subscription Table
CREATE TABLE IF NOT EXISTS subscription(
    subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_status TEXT CHECK(subscription_status IN ('active', 'expired')) NOT NULL,
    subscription_start DATE NOT NULL,
    subscription_end DATE NOT NULL,
    organization_id INT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organization(organization_id)
);

--Activities Table
CREATE TABLE IF NOT EXISTS activity (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_by VARCHAR(50) NOT NULL,
    title VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    due_date DATETIME NOT NULL,
    program_id INTEGER NOT NULL,
    FOREIGN KEY (program_id) REFERENCES program(program_id)
);


--When user participates in a program, completes an activity, 
--reports a sigting, records will be stored in contribution table
--to track user activities in platform
CREATE TABLE IF NOT EXISTS submission(
    submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission BLOB,
    submission_date DATETIME NOT NULL,
    grade REAL,
    teacher_note TEXT,
    activity_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (activity_id) REFERENCES activity(activity_id),
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE IF NOT EXISTS post(
    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_date DATETIME NOT NULL,
    description TEXT,
    post BLOB,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE IF NOT EXISTS comment(
    comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    comment_date DATETIME NOT NULL,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (post_id) REFERENCES post(post_id),
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);
*/
