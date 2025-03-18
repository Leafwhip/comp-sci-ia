# import the other python files
import image_processing
import text_processing
import face_processing
import database_manager

# Pillow allows TKinter to display a wider variety of file types
from PIL import Image, ImageTk

# TKinter is the primary GUI library
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox

# allows for better resolution of the gui on high-dpi displays
# without this line, the gui becomes blurry
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(1)

# os is used for reading the user's file input
import os

import re

def process_image(filepath):
    if text_processing.validate_path(filepath):
        if database_manager.is_photo_in_database(filepath):
            print('Photo already exists in database')
        else:
            folder_path = os.path.dirname(filepath)
            location, timestamp = image_processing.get_image_metadata(filepath)
            tags = image_processing.detect_image(filepath)
            database_manager.add_photo_to_database(filepath, folder_path, location, timestamp, tags)
    else:
        print('Invalid file path')

def process_folder(folder_path):
    print(folder_path)
    # iterate through files in the folder
    for filename in os.listdir(folder_path):
        # analyze every file in the folder
        filepath = os.path.join(folder_path, filename)
        process_image(filepath)

# (for testing) adds an image/video selected by the user to the database
def open_file():
    # open a dialog to choose a file
    filepath = filedialog.askopenfilename()

    # make sure a file is selected and analyze it if it is
    if os.path.isfile(filepath):
        process_image(filepath)
    else:
        print("No file selected")

# (for testing) adds every image/video in a folder selected by the user to the database
def open_folder():
    # open a dialog to choose a folder
    folder_path = filedialog.askdirectory(title="Select a Folder")

    # make sure the user selected a directory (folder)
    if folder_path:
        process_folder(folder_path)
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
    request_output = text_processing.process_input(input, valid_tags, database_manager.get_use_metadata())

    # run the algorithm which finds the images with the most similar tags to the ones given by LLaMa
    photos = database_manager.get_all_photos()
    photo_paths = text_processing.search(photos, request_output, database_manager.get_max_photos())

    # display the images to the canvas
    display_photos(photo_paths)

    # prevent a newline from displaying if the user pressed Enter to submit
    return 'break'

def open_image_details(filepath, photo_paths, current_index):
    details_window = tk.Toplevel(window)
    details_window.title('Image Details')
    details_window.geometry('1152x648+100+100')

    image = Image.open(filepath)
    image.thumbnail((512, 512))
    tk_image = ImageTk.PhotoImage(image)
    container_label = tk.Label(details_window, image=tk_image)
    container_label.image = tk_image
    container_label.pack()

    def open_new_image_details(forward_bool):
        increment = 1 if forward_bool else -1
        open_image_details(photo_paths[current_index + increment], photo_paths, current_index + increment)
        details_window.destroy()

    button_frame = tk.Frame(details_window)
    button_frame.pack(fill='both', expand=True)

    left_button = tk.Button(button_frame, text="←", command=lambda: open_new_image_details(False))
    left_button.pack(side='left', padx=20)
    if current_index == 0:
        left_button.config(state='disabled')

    right_button = tk.Button(button_frame, text="→", command=lambda: open_new_image_details(True))
    right_button.pack(side='right', padx=20)
    if current_index == len(photo_paths) - 1:
        right_button.config(state='disabled')

    filepath_label = tk.Label(details_window, text=f'Filepath: {filepath}')
    filepath_label.pack()
    location, timestamp = database_manager.get_photo(filepath)
    if(location):
        readable_location = text_processing.location_to_readable(location)
        location_label = tk.Label(details_window, text=f'Location that the image was taken: {readable_location}')
        location_label.pack()
    if(timestamp):
        readable_timestamp = text_processing.timestamp_to_readable(timestamp)
        timestamp_label = tk.Label(details_window, text=f'Date the image was taken: {readable_timestamp}')
        timestamp_label.pack()

    find_faces_button = tk.Button(details_window, text='Find Faces', command=lambda: face_processing.find_faces_in_image(filepath))
    find_faces_button.pack()
    

# takes a list of filepaths as input and displays them to the canvas
def display_photos(photo_paths):
    for image in gallery_frame.winfo_children():
        image.destroy()

    gallery_frame.image_refs = []

    for index, filepath in enumerate(photo_paths):
        print(filepath)
        image = Image.open(filepath)
        image.thumbnail((256, 256))
        tk_image = ImageTk.PhotoImage(image)
        container_label = tk.Label(gallery_frame, image=tk_image)
        container_label.pack(padx=5, pady=5)
        container_label.filepath = filepath
        container_label.index = index
        container_label.bind('<Button-1>', lambda e: open_image_details(e.widget.filepath, photo_paths, e.widget.index))
        gallery_frame.image_refs.append(tk_image)

def open_settings():
    settings_window = tk.Toplevel(window)
    settings_window.title('AI Image Finder Settings')
    settings_window.geometry('1152x648')

    is_checked = tk.BooleanVar(value=database_manager.get_use_metadata())
    metadata_checkbox = tk.Checkbutton(settings_window, text='Use metadata? (Takes longer but gives more accurate results)', variable=is_checked, command=lambda: database_manager.set_use_metadata(is_checked.get()))
    metadata_checkbox.pack(pady=10)

    max_photos_label = tk.Label(settings_window, text='Select the number of images to display:')
    max_photos_label.pack()

    max_photos_values = [10, 25, 50, 75, 100]
    max_photos_combobox = ttk.Combobox(settings_window, values=max_photos_values, state='readonly')
    max_photos_combobox.pack(pady=20)
    max_photos_combobox.current(max_photos_values.index(database_manager.get_max_photos()))
    max_photos_combobox.bind('<<ComboboxSelected>>', lambda _: database_manager.set_max_photos(int(max_photos_combobox.get())))

    def add_folder():
        last_opened_dir = database_manager.get_last_opened_dir()
        # open a dialog to choose a folder
        folder_path = filedialog.askdirectory(parent=settings_window, initialdir=last_opened_dir or '/', title='Select a Folder')

        # make sure the user selected a directory (folder)
        if folder_path:
            folders_listbox.insert(tk.END, folder_path)
            database_manager.add_folder(folder_path)
            last_opened_dir = os.path.dirname(folder_path)
            database_manager.set_last_opened_dir(last_opened_dir)
        else:
            print("No folder selected")

    def select_folder():
        remove_folder_button.config(state=tk.ACTIVE)
        process_folder_button.config(state=tk.ACTIVE)

    def deselect_folder():
        remove_folder_button.config(state=tk.DISABLED)
        process_folder_button.config(state=tk.DISABLED)
        folders_listbox.selection_clear(0, tk.END)

    def remove_selected_folder():
        selected_index = folders_listbox.curselection()
        if selected_index:
            database_manager.remove_folder(folders_listbox.get(selected_index))
            folders_listbox.delete(selected_index)
            deselect_folder()

    def process_selected_folder():
        selected_index = folders_listbox.curselection()
        if selected_index:
            if messagebox.askokcancel('Confirm', 'Are you sure you want to process this folder? This may take a while depending on the size of the folder.', parent=settings_window):
                process_folder(folders_listbox.get(selected_index))
                deselect_folder()
        
    folders_label = tk.Label(settings_window, text='List of inputted folders:')
    folders_label.pack()

    folders_listbox = tk.Listbox(settings_window, width=50)
    folders_listbox.pack(pady=10)
    folders_list = database_manager.get_folders()
    for folder_path in folders_list:
        folders_listbox.insert(tk.END, folder_path)
    folders_listbox.bind('<<ListboxSelect>>', lambda _: select_folder())

    buttons_frame = tk.Frame(settings_window)
    buttons_frame.pack()

    add_folder_button = tk.Button(buttons_frame, text='Add Folder', command=lambda: add_folder())
    add_folder_button.pack(padx=10, pady=10, side=tk.LEFT)

    remove_folder_button = tk.Button(buttons_frame, text='Remove Folder', command=lambda: remove_selected_folder())
    remove_folder_button.pack(padx=10, pady=10, side=tk.LEFT)
    remove_folder_button.config(state=tk.DISABLED)

    process_folder_button = tk.Button(buttons_frame, text='Process Folder', command=lambda: process_selected_folder())
    process_folder_button.pack(padx=10, pady=10, side=tk.LEFT)
    process_folder_button.config(state=tk.DISABLED)

# initialize the database
database_manager.init_database()

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
input_text.bind('<Return>', lambda _: submit())

# button which submits the user's request
submit_button = tk.Button(window, text='submit', command=submit)
submit_button.pack()

# (for testing) lets the user add one file to the database, Also prints the image's metadata
upload_image_button = tk.Button(window, text='upload file', command=open_file)
upload_image_button.pack()

# (for testing) lets the user add one folder to the database
upload_folder_button = tk.Button(window, text='upload folder', command=open_folder)
upload_folder_button.pack()

reset_database_button = tk.Button(window, text='reset database', command=database_manager.reset_database)
reset_database_button.pack()

# (for testing) lets the user input an image of a face and name it
#upload_face_button = tk.Button(window, text='upload face', command=face_processing.upload_face)
#upload_face_button.pack()

settings_button = tk.Button(window, text='⚙', width=3, height=1, command=open_settings)
settings_button.place(x=10, y=10)

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