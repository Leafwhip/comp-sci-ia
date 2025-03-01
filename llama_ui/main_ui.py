# import the other python files
import image_processing
import text_processing
import database_manager

# Pillow allows TKinter to display a wider variety of file types
from PIL import Image, ImageTk

# TKinter is the primary GUI library
import tkinter as tk
# for some reason, tk.filedialog doesn't work so it needs to be imported separately
from tkinter import filedialog

# allows for better resolution of the gui on high-dpi displays
# without this line, the gui becomes blurry
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(1)

# os is used for reading the user's file input
import os

# (for testing) adds an image/video selected by the user to the database
def open_file():
    # open a dialog to choose a file
    filepath = filedialog.askopenfilename()

    # make sure a file is selected and analyze it if it is
    if os.path.isfile(filepath):
        if text_processing.validate_path(filepath):
            tags = image_processing.detect_image(filepath)
            database_manager.add_photo_to_database(filepath, None, None, tags)
    else:
        print("No file selected")

# (for testing) adds every image/video in a folder selected by the user to the database
def open_folder():
    # open a dialog to choose a folder
    folder_path = filedialog.askdirectory(title="Select a Folder")

    # make sure the user selected a directory (folder)
    if folder_path:
        # iterate through files in the folder
        for filename in os.listdir(folder_path):
            # analyze every file in the folder
            filepath = os.path.join(folder_path, filename)
            if text_processing.validate_path(filepath):
                tags = image_processing.detect_image(filepath)
                database_manager.add_photo_to_database(filepath, None, None, tags)
    else:
        print("No folder selected")

# runs when the user submits their request
def submit():
    # get the text from the text area
    input = input_text.get('1.0', tk.END)

    # clear the text area
    input_text.delete('1.0', tk.END)

    # get the tags used by YOLO11
    valid_tags = [tag for tag in image_processing.model.names.values()]

    # sends it to the LLM
    output_tags = text_processing.process_input(input, valid_tags)

    # run the algorithm which finds the images with the most similar tags to the ones given by LLaMa
    photos = database_manager.get_photos()
    photo_paths = text_processing.search(photos, output_tags, 10)

    # display the images to the canvas
    display_photos(photo_paths)

# takes a list of filepaths as input and displays them to the canvas
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

# initialize the database
database_manager.initDatabase()

# initialize the window's dimensions and title
window = tk.Tk()
window.geometry('1920x1080')
window.title('AI Image Finder')

# sets the window's icon to icon.png
icon = ImageTk.PhotoImage(Image.open('icon.png'))
window.iconphoto(True, icon)

# text label above the main textbox
input_label = tk.Label(window, text='Enter your image request below:')
input_label.pack()

# the text area where the user can input their request
input_text = tk.Text(window, font=('Calibri', 12), height=5, width=100, padx=5, pady=5)
input_text.pack()

# button which submits the user's request
submit_button = tk.Button(window, text='submit', command=submit)
submit_button.pack()

# (for testing) lets the user add one file to the database
upload_image_button = tk.Button(window, text='upload file', command=open_file)
upload_image_button.pack()

# (for testing) lets the user add one folder to the database
upload_folder_button = tk.Button(window, text='upload folder', command=open_folder)
upload_folder_button.pack()

# creates the Canvas, a TKinter widget that can hold a scrollbar
canvas = tk.Canvas(window)
scrollbar = tk.Scrollbar(window, command=canvas.yview)
canvas.config(yscrollcommand=scrollbar.set)

# creates the scrollbar and adds it to the right side of the canvas
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
canvas.pack(fill=tk.BOTH, expand=True)

# creates the frame widget which can hold multiple images
gallery_frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=gallery_frame, anchor='nw')

# updates the scrollbar to fit the canvas, required for applications which use canvas and scrollbar
def update_scroll_region(_):
    canvas.config(scrollregion=canvas.bbox('all'))

gallery_frame.bind('<Configure>', update_scroll_region)

# displays the window
window.mainloop()