# SQLite3 has the functionality of SQL through Python
import sqlite3

# initializes the SQLite3 database which stores data about images
def initDatabase():
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # creates the photos table with an id, the path to the image, and optionally the time and location of the image
    cursor.execute('''CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT NOT NULL,
            location TEXT,
            timestamp TEXT
            )''')

    # creates the tags table which identifies every tag detected in an image (needed to retrieve data about images)
    cursor.execute('''CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT UNIQUE NOT NULL
            )''')

    # creates the image_tags table which matches each image to one or more tags
    cursor.execute('''CREATE TABLE IF NOT EXISTS image_tags (
            image_id INTEGER,
            tag_id INTEGER
            )''')

    # commit the changes and close the connection
    conn.commit()
    conn.close()

# clears all tables from the database
def resetDatabase():
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # clears the tables in the database
    cursor.execute('DELETE FROM photos')
    cursor.execute('DELETE FROM tags')
    cursor.execute('DELETE FROM image_tags')

    # commit the changes and close the connection
    conn.commit()
    conn.close()

# returns the data from every photo in the database
def get_photos():
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # sets the photos variable to a list of tuples corresponding to every row in the photos table from the database
    cursor.execute("SELECT * FROM photos")
    photos = cursor.fetchall()

    # stores the data about each photo
    # each entry in the list will be a tuple (filepath: str, location: str, timestamp: str, tags: list[str])
    photo_tags = []

    for photo in photos:
        # unpack the data from the photo tuple
        (id, filepath, location, timestamp) = photo

        # sets the data variable to a list of tuples (image_id: int, tag: str) and maps it to a list of only the tags
        # this creates a list of every tag associated with that image
        cursor.execute('SELECT * FROM image_tags WHERE image_id = ?', (id,))
        data = cursor.fetchall()
        tags = [tag[1] for tag in data]

        # add this data to a tuple and append it to the photo_tags list
        photo_tags.append((filepath, location, timestamp, tags))

    # close the connection to the database
    conn.close()

    return photo_tags

# adds a photo to the database once it's detected
def add_photo_to_database(filepath, location, timestamp, tags):
    # connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # add the data from the image to the photos table
    cursor.execute('INSERT INTO photos (filepath, location, timestamp) VALUES (?, ?, ?)', (filepath, location, timestamp))

    # iterate through tags and add each entry to the image_tags database
    for tag in tags:
        # if the tag isn't already in the tags table, add it
        cursor.execute('INSERT OR IGNORE INTO tags (tag) VALUES (?)', (tag,))

        # get the size of the photos table
        cursor.execute('SELECT MAX(id) FROM photos')
        max_id = cursor.fetchone()
        
        # add a connection from the image id to the tag
        # this allows one image to be associated with multiple tags
        cursor.execute('INSERT INTO image_tags (image_id, tag_id) VALUES (?, ?)', (max_id[0], tag))

    # commit the changes and close the connection
    conn.commit()
    conn.close()