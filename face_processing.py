import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from PIL import Image
import database_manager

import re

# initialize the FaceAnalysis model
app = FaceAnalysis(name='buffalo_l')
app.prepare(ctx_id=0, det_size=(640, 640))

def validate_path(filepath):
    # valid file extensions
    valid_extensions = {'webp', 'tif', 'tiff', 'jpg', 'bmp', 'png', 'jpeg'}

    # get the file extension of the filepath
    file_type = re.split(r'\.', filepath)[-1]
    
    # make sure the file extension is compatible with insightface
    if file_type in valid_extensions:
        return True
    
    return False

def cosine_similarity(embedding1, embedding2):
    return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))

def detect_image(filepath):
    if validate_path(filepath):
        image = cv2.imread(filepath)
        faces = app.get(image)
    
        return image, faces
    else:
        print('This file is not supported by InsightFace')

def get_face_thumbnails(image, faces):
    face_thumbnails = []
    for face in faces:
        x1, y1, x2, y2 = face.bbox.astype(int)
        cropped_face = image[y1:y2, x1:x2]
        cropped_face = cv2.cvtColor(cropped_face, cv2.COLOR_BGR2RGB)
        face_image = Image.fromarray(cropped_face)
        face_image.thumbnail((128, 128))
        face_thumbnails.append(face_image)
    
    return face_thumbnails

def label_faces(faces):
    face_labels = []
    saved_faces = database_manager.get_faces()
    saved_faces = [(name, blob_to_embedding(embedding)) for name, embedding in saved_faces]

    for face1 in faces:
        embedding1 = face1.normed_embedding
        match_found = False

        for face2 in saved_faces:
            name, embedding2 = face2
            similarity = cosine_similarity(embedding1, embedding2)
            if similarity > 0.5:
                face_labels.append(name)
                match_found = True

        if not match_found:
            face_labels.append(None)
    
    return face_labels     

def embedding_to_blob(embedding):
    return embedding.astype(np.float32).tobytes()

def blob_to_embedding(embedding_as_blob):
    return np.frombuffer(embedding_as_blob, dtype=np.float32)
