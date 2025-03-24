# YOLO is the image processing AI
from ultralytics import YOLO

from PIL import Image, ExifTags

import re

# instantiate the YOLO model
model = YOLO('yolo11n.pt')

# returns a set of tags detected in an image/video file
def detect_image(filepath):
    # YOLO11 analyzes the image
    results = model(source=filepath, stream=True)

    # create a set of tags
    # must be a set because multiple of the same tag could be detected
    tags = set()

    # add every detected tag to the tags list
    for r in results:
        for box in r.boxes:
            # cls_id is an integer that represents a tag
            cls_id = int(box.cls)

            # get the name of the tag as a string
            tag_name = model.names[cls_id]

            # add the tag to the set
            tags.add(tag_name)

    return list(tags)

# gets the location and timestamp from a file
def get_image_metadata(filepath):
    img = Image.open(filepath)

    # get the image's EXIF data (its metadata)
    exif_data = img._getexif()

    location = {}
    timestamp = ''

    if not exif_data:
        print('Image does not contain EXIF data.')
        return (None, None)

    # get the location and timestamp from EXIF data
    for key, value in exif_data.items():
        if ExifTags.TAGS[key] == 'GPSInfo':
            location = value
        if ExifTags.TAGS[key] == 'DateTime':
            timestamp = value
    
    # set location to None if EXIF data exists but GPSInfo doesn't
    if location:
        # parse the gps info to more useful coordinates
        # turns DMS (Degrees, Minutes, Secons) to decimal degrees
        # using the formula: decimal degrees = degrees + minutes / 60 + seconds / 3600
        latitude_dir, latitude_dms, longitude_dir, longitude_dms, _, _ = (val for val in location.values())
        latitude_deg = float(latitude_dms[0] + latitude_dms[1] / 60 + latitude_dms[2] / 3600)
        if latitude_dir == 'S':
            latitude_deg *= -1
        longitude_deg = float(longitude_dms[0] + longitude_dms[1] / 60 + longitude_dms[2] / 3600)
        if longitude_dir == 'W':
            longitude_deg *= -1
        
        latitude_deg = round(latitude_deg, 4)
        longitude_deg = round(longitude_deg, 4)
        
        location = f'{latitude_deg},{longitude_deg}'
    else:
        location = None
    
    # set timestamp to None if EXIF data exists but DateTime doesn't
    timestamp = timestamp if timestamp else None
            
    return (location, timestamp)