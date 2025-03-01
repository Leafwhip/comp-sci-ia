# YOLO is the image processing AI
from ultralytics import YOLO

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

    return tags