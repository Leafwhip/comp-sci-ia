import text_processing
import image_processing
import face_processing
import database_manager

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

import os

# this is the UI that is created when the user opens the settings
class SettingsUI:
    def __init__(self, parent):
        self.parent = parent

        # create the settings window
        self.settings_window = tk.Toplevel(self.parent)
        self.settings_window.title('AI Image Finder Settings')
        self.settings_window.geometry('1152x648')

        # create the checkbox to toggle metadata in searches
        self.is_checked = tk.BooleanVar(value=database_manager.get_use_metadata())
        self.metadata_checkbox = tk.Checkbutton(self.settings_window, text='Use metadata? (Takes longer but gives more accurate results)', variable=self.is_checked, command=lambda: database_manager.set_use_metadata(self.is_checked.get()))
        self.metadata_checkbox.pack(pady=10)

        # label for the max photos combobox
        self.max_photos_label = tk.Label(self.settings_window, text='Select the number of images to display:')
        self.max_photos_label.pack()

        # create the max photos combobox
        # changes the maximum number of photos that will be displayed
        max_photos_values = [10, 25, 50, 75, 100]
        self.max_photos_combobox = ttk.Combobox(self.settings_window, values=max_photos_values, state='readonly')
        self.max_photos_combobox.pack(pady=20)
        self.max_photos_combobox.current(max_photos_values.index(database_manager.get_max_photos()))
        self.max_photos_combobox.bind('<<ComboboxSelected>>', lambda _: database_manager.set_max_photos(int(self.max_photos_combobox.get())))
        
        # label for folder input
        self.folders_label = tk.Label(self.settings_window, text='List of inputted folders:')
        self.folders_label.pack()

        # create the listbox to hold inputted folders
        self.folders_listbox = tk.Listbox(self.settings_window, width=50)
        self.folders_listbox.pack(pady=10)
        # load previously added folders
        folders_list = database_manager.get_folders()
        for folder_path in folders_list:
            self.folders_listbox.insert(tk.END, folder_path)
        self.folders_listbox.bind('<<ListboxSelect>>', lambda _: self.select_folder())

        # create the frame that holds the buttons side by side
        self.buttons_frame = tk.Frame(self.settings_window)
        self.buttons_frame.pack()

        # button that inputs folder
        self.add_folder_button = tk.Button(self.buttons_frame, text='Add Folder', command=lambda: self.add_folder())
        self.add_folder_button.pack(padx=10, pady=10, side=tk.LEFT)

        # button that removes the selected folder
        # disabled when no folder is selected
        self.remove_folder_button = tk.Button(self.buttons_frame, text='Remove Folder', command=lambda: self.remove_selected_folder())
        self.remove_folder_button.pack(padx=10, pady=10, side=tk.LEFT)
        self.remove_folder_button.config(state=tk.DISABLED)

        # button that processes the selected folder
        # disabled when no folder is selected
        self.process_folder_button = tk.Button(self.buttons_frame, text='Process Folder', command=lambda: self.process_selected_folder(False))
        self.process_folder_button.pack(padx=10, pady=10, side=tk.LEFT)
        self.process_folder_button.config(state=tk.DISABLED)

        # button that reprocesses the selected folder (doesn't skip over already processed files)
        # disabled when no folder is selected
        self.reprocess_folder_button = tk.Button(self.buttons_frame, text='Reprocess Folder', command=lambda: self.process_selected_folder(True))
        self.reprocess_folder_button.pack(padx=10, pady=10, side=tk.LEFT)
        self.reprocess_folder_button.config(state=tk.DISABLED)

        # button that cancels the processing of a folder
        self.processing_disabled = True
        self.cancel_processing_button = tk.Button(self.buttons_frame, text='Cancel Processing', command=lambda: self.cancel_processing())
        self.cancel_processing_button.pack(padx=10, pady=10, side=tk.LEFT)
        self.cancel_processing_button.config(state=tk.DISABLED)

    # asks user to input a folder and adds it to the listbox and database
    def add_folder(self):
        # start the file search from where it was last opened
        last_opened_dir = database_manager.get_last_opened_dir()
        # open a dialog to choose a folder
        folder_path = filedialog.askdirectory(parent=self.settings_window, initialdir=last_opened_dir or '/', title='Select a Folder')

        # make sure the user selected a directory (folder)
        if os.path.isdir(folder_path):
            # add the folder to the listbox and database
            self.folders_listbox.insert(tk.END, folder_path)
            database_manager.add_folder(folder_path)
            last_opened_dir = os.path.dirname(folder_path)
            database_manager.set_last_opened_dir(last_opened_dir)
        else:
            print("No folder selected")

    # runs when the user selects a folder in the listbox
    def select_folder(self):
        # activate the buttons
        self.remove_folder_button.config(state=tk.ACTIVE)
        self.process_folder_button.config(state=tk.ACTIVE)
        self.reprocess_folder_button.config(state=tk.ACTIVE)

    # runs after removing or processing a folder
    def deselect_folder(self):
        # deactivate the buttons
        self.remove_folder_button.config(state=tk.DISABLED)
        self.process_folder_button.config(state=tk.DISABLED)
        self.reprocess_folder_button.config(state=tk.DISABLED)
        self.cancel_processing_button.config(state=tk.DISABLED)
        # deselect the selected folder
        self.folders_listbox.selection_clear(0, tk.END)

    # removes the selected folder
    def remove_selected_folder(self):
        # make sure a folder is selected
        selected_index = self.folders_listbox.curselection()
        if selected_index:
            # remove the folder from the database and listbox
            database_manager.remove_folder(self.folders_listbox.get(selected_index))
            self.folders_listbox.delete(selected_index)
            self.deselect_folder()

    # process every image in the selected folder
    def process_selected_folder(self, reprocess):
        selected_index = self.folders_listbox.curselection()
        if selected_index:
            # make the user confirm that they want to process the folder
            if messagebox.askokcancel('Confirm', 'Are you sure you want to process this folder? This may take a while depending on the size of the folder.', parent=self.settings_window):
                # enable the cancel processing button
                self.processing_disabled = False
                self.cancel_processing_button.config(state=tk.ACTIVE)

                folder_path = self.folders_listbox.get(selected_index)
                file_list = os.listdir(folder_path)
                self.process_folder(folder_path, file_list, 0, reprocess)

    # process the selected folder
    def process_folder(self, folder_path, file_list, index, reprocess):
        if index < len(file_list) and not self.processing_disabled:
            file_name = file_list[index]
            filepath = os.path.join(folder_path, file_name)
            self.process_image(filepath, reprocess)
            self.folders_label.config(text=f'Processing {file_name} ({index + 1}/{len(file_list)})')
            
            # process the next file in the folder
            self.parent.after(25, self.process_folder, folder_path, file_list, index + 1, reprocess)
        else:
            # alert the user that processing has completed
            messagebox.showinfo('Alert', 'Processing has finished.', parent=self.settings_window)
            self.folders_label.config(text='List of inputted folders:')
            self.deselect_folder()

    # process a single image in a folder
    def process_image(self, filepath, reprocess):
        # validate the filepath
        if image_processing.validate_path(filepath):
            # don't process if it has already been processed
            if database_manager.is_photo_in_database(filepath) and not reprocess:
                print('Photo already exists in database')
            else:
                print(f'Processing: {filepath}')
                # get all the image data (tags and faces)
                folder_path = os.path.dirname(filepath)
                location, timestamp = image_processing.get_image_metadata(filepath)
                tags = image_processing.detect_image(filepath)
                faces = face_processing.detect_image(filepath)[1]
                face_tags = list(set(face_processing.label_faces(faces)))
                face_tags = [name for name in face_tags if name]
                tags += face_tags
                # add it to the database
                database_manager.add_photo_to_database(filepath, folder_path, location, timestamp, tags)
        else:
            print('This file is not supported by YOLO')
        
    # cancel the processing of a folder
    def cancel_processing(self):
        self.processing_disabled = True
        