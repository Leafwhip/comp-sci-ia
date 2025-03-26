import text_processing
import face_processing
import database_manager

import tkinter as tk
from tkinter import simpledialog
from PIL import Image, ImageTk

# this is the UI that is created when the user clicks on an image in the gallery frame
# contains a more detailed view of the image and has face recognition functionality
class DetailsUI:
    def __init__(self, parent, filepath, photo_paths, current_index):
        self.parent = parent
        # the path to the image being displayed
        self.filepath = filepath
        # the full list of filepaths to photos being displayed in the gallery frame
        self.photo_paths = photo_paths
        # the index of this photo in the list of photo paths
        self.current_index = current_index

        # create the main details window
        self.details_window = tk.Toplevel(self.parent)
        self.details_window.title('Image Details')
        self.details_window.geometry('1728x972+100+100')

        # display the image
        image = Image.open(self.filepath)
        image.thumbnail((512, 512))
        tk_image = ImageTk.PhotoImage(image)
        self.image_container_label = tk.Label(self.details_window, image=tk_image)
        self.image_container_label.image = tk_image
        self.image_container_label.pack()
        
        # create left and right buttons to move through photo_paths
        self.button_frame = tk.Frame(self.details_window)
        self.button_frame.pack(fill='x')

        self.left_button = tk.Button(self.button_frame, text="←", command=lambda: self.open_new_image_details(False))
        self.left_button.pack(side='left', padx=20)
        if self.current_index == 0:
            self.left_button.config(state='disabled')

        self.right_button = tk.Button(self.button_frame, text="→", command=lambda: self.open_new_image_details(True))
        self.right_button.pack(side='right', padx=20)
        if self.current_index == len(self.photo_paths) - 1:
            self.right_button.config(state='disabled')

        # show the location and timestamp if they exist
        self.filepath_label = tk.Label(self.details_window, text=f'Filepath: {self.filepath}')
        self.filepath_label.pack()
        location, timestamp = database_manager.get_photo(self.filepath)
        if(location):
            readable_location = text_processing.location_to_readable(location)
            self.location_label = tk.Label(self.details_window, text=f'Location that the image was taken: {readable_location}')
            self.location_label.pack()
        if(timestamp):
            readable_timestamp = text_processing.timestamp_to_readable(timestamp)
            self.timestamp_label = tk.Label(self.details_window, text=f'Date the image was taken: {readable_timestamp}')
            self.timestamp_label.pack()
        
        # frame to hold every detected face and name
        self.face_thumbnail_frame = tk.Frame(self.details_window)
        self.face_thumbnail_frame.pack(fill='x')

        self.find_faces_button = tk.Button(self.details_window, text='Find Faces', command=lambda: self.find_faces())
        self.find_faces_button.pack()
    
    # opens a new details window
    # runs when arrow buttons are pressed
    def open_new_image_details(self, forward_bool):
        # change the index and open a new details window
        increment = 1 if forward_bool else -1
        DetailsUI(self.parent, self.photo_paths[self.current_index + increment], self.photo_paths, self.current_index + increment)
        # close the current details window
        self.details_window.destroy()

    # opens a dialog window to input a name
    # runs when the user clicks a face thumbnail
    def ask_save_face(self, widget):
        name = simpledialog.askstring('', 'Enter this person\'s name, or leave blank to cancel', parent=self.details_window)
        if name is not None:
            # if the user inputted a name, add it to the database
            database_manager.add_face_to_database(name, face_processing.embedding_to_blob(widget.embedding), widget.name)
            widget.config(text=name)
            widget.name = name

    # show the faces in the image
    def find_faces(self):
        # detect the faces
        cv_image, faces = face_processing.detect_image(self.filepath)
        # get Pillow images of each face
        face_thumbnails = face_processing.get_face_thumbnails(cv_image, faces)
        # label the faces if a match exists in the database
        face_labels = face_processing.label_faces(faces)
        
        # for each face, create a label which holds its image and name
        for index, image in enumerate(face_thumbnails):
            tk_image = ImageTk.PhotoImage(image)
            face_name = face_labels[index]
            container_label = tk.Label(self.face_thumbnail_frame, image=tk_image, text=face_name or '???', compound='bottom')
            # store tk_image in the label
            # without this line, the image gets garbage collected and fails to display
            container_label.image = tk_image
            container_label.embedding = faces[index].normed_embedding
            container_label.name = face_name
            container_label.pack(padx=5, pady=5, side=tk.LEFT)
            # when the user clicks the image, run ask_save_face
            container_label.bind('<Button-1>', lambda e: self.ask_save_face(e.widget))
        
        # disable the button
        self.find_faces_button.config(state='disabled')