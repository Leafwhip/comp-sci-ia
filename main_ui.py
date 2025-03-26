# import the other python files
import text_processing
import database_manager
import settings_ui
import details_ui

# Pillow allows TKinter to display a wider variety of file types
from PIL import Image, ImageTk

# TKinter is the primary GUI library
import tkinter as tk

# allows for better resolution of the gui on high-dpi displays
# without this line, the gui becomes blurry
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(1)

# main UI class
class MainUI:
    def __init__(self):
        # initialize the database
        database_manager.init_database()

        # initialize the window's dimensions and title
        self.window = tk.Tk()
        self.window.geometry('1920x1080')
        self.window.title('AI Image Finder')

        # text label above the main textbox
        self.input_label = tk.Label(self.window, text='Enter your image request below:')
        self.input_label.pack()

        # the text area where the user can input their request
        self.input_text = tk.Text(self.window, font=('Calibri', 12), height=5, width=100, padx=5, pady=5)
        self.input_text.pack()
        self.input_text.bind('<Return>', lambda _: self.submit())

        # button which submits the user's request
        self.submit_button = tk.Button(self.window, text='submit', command=self.submit)
        self.submit_button.pack()

        # for testing ofc. remove this <3
        self.reset_database_button = tk.Button(self.window, text='reset database', command=database_manager.reset_database)
        self.reset_database_button.pack()

        # button which opens settings (located on top left)
        self.settings_button = tk.Button(self.window, text='⚙', width=3, height=1, command=self.open_settings)
        self.settings_button.place(x=10, y=10)

        # creates the Canvas, a TKinter widget that can hold a scrollbar
        self.canvas = tk.Canvas(self.window)
        self.scrollbar = tk.Scrollbar(self.window, command=self.canvas.yview)
        self.canvas.config(yscrollcommand=self.scrollbar.set)

        # creates the scrollbar and adds it to the right side of the canvas
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # creates the frame widget which can hold multiple images
        self.gallery_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.gallery_frame, anchor='nw')
        # when the frame is resized, the scrollbar also updates
        self.gallery_frame.bind('<Configure>', self.update_scroll_region)

        # displays the window
        self.window.mainloop()

    # updates the scrollbar to fit the canvas, required for applications which use canvas and scrollbar
    def update_scroll_region(self, _):
        self.canvas.config(scrollregion=self.canvas.bbox('all'))

    # runs when the user submits their request
    def submit(self):
        # get the text from the text area
        input = self.input_text.get('1.0', tk.END)

        # clear the text area
        self.input_text.delete('1.0', tk.END)

        # get the tags used by YOLO11 
        valid_tags = database_manager.get_found_tags()
        # sends it to the LLM
        request_output = text_processing.process_input(input, valid_tags, database_manager.get_use_metadata())

        # run the algorithm which finds the images with the most similar tags to the ones given by LLaMa
        photos = database_manager.get_all_photos()
        photo_paths = text_processing.search(photos, request_output, database_manager.get_max_photos())

        # display the images to the canvas
        self.display_photos(photo_paths)

        # prevent a newline from displaying if the user pressed Enter to submit
        return 'break'

    # opens an image details window
    # runs when the user clicks on an image thumbnail after searching
    def open_image_details(self, filepath, photo_paths, current_index):
        details_ui.DetailsUI(self.window, filepath, photo_paths, current_index)

    # takes a list of filepaths as input and displays them to the canvas
    def display_photos(self, photo_paths):
        # clears the gallery frame
        for image in self.gallery_frame.winfo_children():
            image.destroy()

        # iterate through photo paths
        for index, filepath in enumerate(photo_paths):
            print(filepath)
            # use Pillow to open the image
            image = Image.open(filepath)
            # set the image's display size
            image.thumbnail((256, 256))

            # PhotoImage is displayable by Tkinter
            tk_image = ImageTk.PhotoImage(image)
        
            # create the label to hold the image
            container_label = tk.Label(self.gallery_frame, image=tk_image)
            container_label.pack(padx=5, pady=5)
            container_label.filepath = filepath
            container_label.index = index
            # store tk_image in the label
            # without this line, the image gets garbage collected and fails to display
            container_label.image = tk_image
            # when the user clicks the image, open an image details window
            container_label.bind('<Button-1>', lambda e: self.open_image_details(e.widget.filepath, photo_paths, e.widget.index))

    # opens the settings window
    def open_settings(self):
        settings_ui.SettingsUI(self.window)

MainUI()