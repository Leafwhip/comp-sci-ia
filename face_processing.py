import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis

app = FaceAnalysis()
app.prepare(ctx_id=0, det_size=(640, 640))

def find_faces_in_image(filepath):
    image_path = filepath
    img = cv2.imread(image_path)

    faces = app.get(img)
    
    for face in faces:
        bbox = face.bbox.astype(int)
        cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)

    cv2.imshow('Detected Faces', img)
    cv2.imwrite('output.jpg', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()