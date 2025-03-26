# SQLite3 has the functionality of SQL through Python
import sqlite3

# initializes the SQLite3 database which stores data about images
def init_database():
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # creates the photos table with the path to the image, and optionally the time and location of the image
    cursor.execute('''CREATE TABLE IF NOT EXISTS photos (
            filepath TEXT UNIQUE NOT NULL,
            folder_path TEXT NOT NULL,
            location TEXT,
            timestamp TEXT
            )''')

    # creates the photo_tags table which matches each image to one or more tags
    cursor.execute('''CREATE TABLE IF NOT EXISTS photo_tags (
            filepath TEXT NOT NULL,
            tag_name TEXT NOT NULL
            )''')
    
    # creates the faces table which contains the name and embeddings of each face
    cursor.execute('''CREATE TABLE IF NOT EXISTS faces (
            name TEXT UNIQUE NOT NULL,
            embedding BLOB NOT NULL
            )''')
    
    # creates the folders table which contains added folders
    cursor.execute('''CREATE TABLE IF NOT EXISTS folders (
            folder_path TEXT UNIQUE NOT NULL
            )''')

    # creates the settings table which contains miscellaneous data
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
            id INTEGER UNIQUE NOT NULL,
            use_metadata BOOLEAN,
            max_photos INTEGER,
            last_opened_dir TEXT
            )''')
    
    # set up the default settings
    cursor.execute('INSERT OR IGNORE INTO settings (id, use_metadata, max_photos, last_opened_dir) VALUES (?, ?, ?, ?)', (1, False, 25, '/'))
    
    # commit the changes and close the connection
    conn.commit()
    conn.close()

# remove all tables from the database (for debugging/modifying tables, should not be used)
def reset_database():
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # remove the tables in the database
    cursor.execute('DROP TABLE IF EXISTS photos')
    cursor.execute('DROP TABLE IF EXISTS tags')
    cursor.execute('DROP TABLE IF EXISTS photo_tags')
    cursor.execute('DROP TABLE IF EXISTS faces')
    cursor.execute('DROP TABLE IF EXISTS folders')
    cursor.execute('DROP TABLE IF EXISTS settings')

    # commit the changes and close the connection
    conn.commit()
    conn.close()

    init_database()

def get_photo(filepath):
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # sets the photos variable to a list of tuples corresponding to every row in the photos table from the database
    cursor.execute('SELECT * FROM photos WHERE filepath = ?', (filepath,))
    data = cursor.fetchone()

    # close the connection to the database
    conn.close()

    return data[2:]

# returns the data from every photo in the database
def get_all_photos():
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # sets the photos variable to a list of tuples corresponding to every row in the photos table from the database
    cursor.execute('SELECT * FROM photos')
    photos = cursor.fetchall()

    # stores the data about each photo
    # each entry in the list will be a tuple (filepath: str, folder_path: str, location: str, timestamp: str, tags: list[str])
    photo_data = []

    for photo in photos:
        # unpack the data from the photo tuple
        filepath, folder_path, location, timestamp = photo

        # get a list of all entries in photo_tags with that filepath
        cursor.execute('SELECT * FROM photo_tags WHERE filepath = ?', (filepath,))
        data = cursor.fetchall()
        tags = [tag[1] for tag in data]

        # add this data to a tuple and append it to the photo_data list
        photo_data.append((filepath, folder_path, location, timestamp, tags))

    # close the connection to the database
    conn.close()

    return photo_data

# get a list of all the tags in the database
def get_found_tags():
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # get every entry in photo_tags and map the list to only tags
    cursor.execute('SELECT * FROM photo_tags')
    photo_tags = cursor.fetchall()
    tags = set([tag[1] for tag in photo_tags])

    # close the connection to the database
    conn.close()

    return tags

# returns True if the filepath exists in the database, otherwise returns False
def is_photo_in_database(filepath):
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Get an entry with the filepath from the database
    cursor.execute('SELECT 1 FROM photos WHERE filepath = ?', (filepath,))
    result = cursor.fetchone()

    # close the connection to the database
    conn.close()

    return True if result else False

# adds a photo to the database once it's detected
def add_photo_to_database(filepath, folder_path, location, timestamp, tags):
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # add the data from the image to the photos table
    cursor.execute('INSERT OR REPLACE INTO photos (filepath, folder_path, location, timestamp) VALUES (?, ?, ?, ?)', (filepath, folder_path.lower(), location, timestamp))

    # remove old tags associated with that filepath before adding new ones
    cursor.execute('DELETE FROM photo_tags WHERE filepath = ?', (filepath,))

    # iterate through tags and add each entry to the photo_tags database
    for tag in tags:        
        # add a connection from the filepath to the tag
        # this allows one photo to be associated with multiple tags
        cursor.execute('INSERT INTO photo_tags (filepath, tag_name) VALUES (?, ?)', (filepath, tag))

    # commit the changes and close the connection
    conn.commit()
    conn.close()

# returns a list of faces (name and embedding) from the database
def get_faces():
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM faces')
    faces = cursor.fetchall()

    # close the connection to the database
    conn.close()

    return faces

# add a name and embedding to the database
def add_face_to_database(name, embedding_as_blob, prev_name):
    print(name, prev_name)
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # delete the data of the old name if exists
    cursor.execute('DELETE FROM faces WHERE name = (?)', (prev_name,))

    # remove all references to the tag
    cursor.execute('DELETE FROM photo_tags WHERE tag_name = ?', (prev_name,))

    # add the name and embedding to the database
    cursor.execute('INSERT OR REPLACE INTO faces (name, embedding) VALUES (?, ?)', (name, embedding_as_blob))

    # commit changes and close the connection
    conn.commit()
    conn.close()

def get_folders():
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # get all the folders
    cursor.execute('SELECT * FROM folders')
    folders = cursor.fetchall()

    # each entry is a tuple so it needs to be converted to string
    folders = [folder[0] for folder in folders]

    # close the connection to the database
    conn.close()

    return folders

# add a folder path to the database
def add_folder(folder_path):
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # add the path to the database
    cursor.execute('INSERT OR IGNORE INTO folders (folder_path) VALUES (?)', (folder_path,))

    # commit changes and close the connection
    conn.commit()
    conn.close()

# remove a folder from the database
def remove_folder(folder_path):
    print(folder_path)
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # delete the folder path from the folders table
    cursor.execute('DELETE FROM folders WHERE folder_path = (?)', (folder_path,))

    # delete all photos with that folder path from the photos table
    cursor.execute('DELETE FROM photos WHERE folder_path = (?)', (folder_path,))

    # commit changes and close the connection
    conn.commit()
    conn.close()

# the rest of these are just various getters and setters
def get_use_metadata():
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM settings')
    data = cursor.fetchone()

    # close the connection to the database
    conn.close()

    return bool(data[1])

def set_use_metadata(use_metadata):
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('UPDATE settings SET use_metadata = ? WHERE id = 1', (use_metadata,))

    conn.commit()
    conn.close()

def get_max_photos():
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM settings')
    data = cursor.fetchone()

    # close the connection to the database
    conn.close()

    return data[2]

def set_max_photos(max_photos):
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('UPDATE settings SET max_photos = ? WHERE id = 1', (max_photos,))

    conn.commit()
    conn.close()

def get_last_opened_dir():
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM settings')
    data = cursor.fetchone()

    # close the connection to the database
    conn.close()

    return data[3]

def set_last_opened_dir(last_opened_dir):
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('UPDATE settings SET last_opened_dir = ? WHERE id = 1', (last_opened_dir,))

    conn.commit()
    conn.close()

def print_table(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # fetch all rows from the table
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    # get column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]

    # print column names
    print(" | ".join(columns))
    print("-" * 50)

    # print rows
    for row in rows:
        print(" | ".join(map(str, row)))

    conn.close()

#print_table('database.db', 'faces')