import os
import ctypes
import re
import tkinter as tk
from PIL import Image, ImageTk
import ollama
from ultralytics import YOLO
import sqlite3

# allows for better resolution of the gui on high-dpi displays
# without this line, the gui becomes blurry
ctypes.windll.shcore.SetProcessDpiAwareness(1)

# instantiate the YOLO model
model = YOLO('yolo11n.pt')


def initDatabase():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT NOT NULL,
            location TEXT,
            timestamp TEXT
            )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT UNIQUE NOT NULL
            )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS image_tags (
            image_id INTEGER,
            tag_id INTEGER
            )''')

    conn.commit()
    conn.close()

initDatabase()

def resetDatabase():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM photos')
    cursor.execute('DELETE FROM tags')
    cursor.execute('DELETE FROM image_tags')

    conn.commit()
    conn.close()

# ai gen function for testing purposes. will be changed/removed
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

print_table('database.db', 'photos')


def get_photos():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM photos")
    photos = cursor.fetchall()

    photo_tags = []

    for photo in photos:
        (id, filepath, location, timestamp) = photo
        cursor.execute('SELECT * FROM image_tags WHERE image_id = ?', (id,))
        data = cursor.fetchall()
        tags = [tag[1] for tag in data]
        photo_tags.append((filepath, location, timestamp, tags))

    conn.close()
    return photo_tags


def search(request_tags, max_photos):
    photos = get_photos()
    photo_scores = []
    for photo_data in photos:
        (filepath, location, timestamp, tags) = photo_data
        match_score = sum([tag in request_tags for tag in tags])
        photo_scores.append((match_score, filepath))
        print(request_tags, tags, match_score)
    
    photo_scores = [photo for photo in photo_scores if photo[0] > 0]
    if(len(photo_scores) == 0):
        print("No photos matched your search")
        return
    
    photo_scores.sort(key=lambda x: x[0], reverse=True)
    best_photos = photo_scores[:max_photos]
    photo_paths = [photo[1] for photo in best_photos]
    display_photos(photo_paths)


def display_photos(photo_paths):
    for image in gallery_frame.winfo_children():
        image.destroy()

    gallery_frame.image_refs = []

    for filepath in photo_paths:
        print(filepath)
        image = Image.open(filepath)
        image.thumbnail((256, 256))
        tk_image = ImageTk.PhotoImage(image)
        container_label = tk.Label(gallery_frame, image=tk_image)
        container_label.pack(padx=5, pady=5)
        gallery_frame.image_refs.append(tk_image)


def input_llama(prompt):
    response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
    return response['message']['content']


def submit():
    input = input_text.get('1.0', tk.END)
    input_text.delete('1.0', tk.END)
    valid_tags = [tag for tag in model.names.values()]
    llama_request = f'Return a list of tags likely to be detected by the computer vision model YOLO11 in a picture described by the prompt below. Return your answer as a list separated by barriers | and surrrounded by square brackets. Return NOTHING except the list of tags.\nOnly use tags from this list: {valid_tags}.\nThe prompt is: {input}'
    
    output = input_llama(llama_request)
    print(llama_request)
    print(output)
    output_tags = re.sub(r'[\r\n]', '', output)
    output_tags = re.match(r'\[.*\]', output_tags)[0]
    output_tags = re.findall(r'(\w+ *\w+)+', output_tags, re.IGNORECASE)
    print(output_tags)
    search(output_tags, 10)


def detect_image(filepath):
    # valid file extensions
    images = {'webp', 'dng', 'tif', 'tiff', 'mpo', 'jpg', 'bmp', 'heic', 'png', 'jpeg', 'pfm'}
    videos = {'mkv', 'ts', 'mp4', 'wmv', 'mpeg', 'asf', 'webm', 'avi', 'm4v', 'mpg', 'mov', 'gif'}

    # if the file extension is invalid, YOLO won't run
    file_type = re.split(r'\.', filepath)[-1]
    if not file_type in images and not file_type in videos:
        print('This file type is not supported')
        return
    results = model(source=filepath, stream=True)
    detected_objects = set()
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls)
            detected_objects.add(model.names[cls_id])

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO photos (filepath) VALUES (?)', (filepath,))
    for tag in detected_objects:
        cursor.execute('INSERT OR IGNORE INTO tags (tag) VALUES (?)', (tag,))
        cursor.execute('SELECT MAX(id) FROM photos')
        max_id = cursor.fetchone()
        cursor.execute('INSERT INTO image_tags (image_id, tag_id) VALUES (?, ?)', (max_id[0], tag))
    conn.commit()
    conn.close()

def open_file():
    # open a dialog to choose a file
    filepath = tk.filedialog.askopenfilename()

    # make sure a file is selected
    if os.path.isfile(filepath):
        detect_image(filepath)
    else:
        print("No file selected")

def open_folder():
    # open a dialog to choose a folder
    folder_path = tk.filedialog.askdirectory(title="Select a Folder")

    # make sure the user selected a directory (folder)
    if folder_path:
        # iterate through files in the folder
        for filename in os.listdir(folder_path):
            filepath = os.path.join(folder_path, filename)
            if os.path.isfile(filepath):
                detect_image(filepath)
    else:
        print("No folder selected")


# initialize the window's dimensions and title
window = tk.Tk()
window.geometry('1920x1080')
window.title('AI Image Finder')

# sets the window's icon to icon.png
icon = ImageTk.PhotoImage(Image.open('icon.png'))
window.iconphoto(True, icon)

input_label = tk.Label(window, text='Enter your image request below:')
input_label.pack()

input_text = tk.Text(window, font=('Calibri', 12), height=5, width=100, padx=5, pady=5)
input_text.pack()
# make the input text submit when the user presses Enter
input_text.bind('<Return>', submit)

submit_button = tk.Button(window, text='submit', command=submit)
submit_button.pack()
    
upload_image_button = tk.Button(window, text='upload file', command=open_file)
upload_image_button.pack()

upload_folder_button = tk.Button(window, text='upload folder', command=open_folder)
upload_folder_button.pack()

canvas = tk.Canvas(window)
scrollbar = tk.Scrollbar(window, command=canvas.yview)
canvas.config(yscrollcommand=scrollbar.set)

scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
canvas.pack(fill=tk.BOTH, expand=True)

gallery_frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=gallery_frame, anchor='nw')

def update_scroll_region():
    canvas.config(scrollregion=canvas.bbox('all'))

gallery_frame.bind('<Configure>', update_scroll_region)

window.mainloop() # displays the window