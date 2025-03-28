# cv2 is required to run InsightFace
import cv2
print("cv2 version:", cv2.__version__)

# numpy is used to calculate cosine similarity
import numpy as np

# InsightFace is the face processing AI
import insightface
from insightface.app import FaceAnalysis

from PIL import Image

import re

import database_manager

# initialize the InsightFace model
app = FaceAnalysis(name='buffalo_l')
app.prepare(ctx_id=0, det_size=(640, 640))

# validate the filepath to make sure it's compatible with InsightFace
def validate_path(filepath):
    # valid file extensions
    valid_extensions = {'webp', 'tif', 'tiff', 'jpg', 'bmp', 'png', 'jpeg'}

    # get the file extension of the filepath
    file_type = re.split(r'\.', filepath)[-1]
    
    # make sure the file extension is compatible with insightface
    if file_type in valid_extensions:
        return True
    
    return False

# embeddings are multi-dimensional vectors
# in linear algebra, the angle between two vectors v1 and v2 is
# v1 • v2 / (||v1|| * ||v2||)
# where • denotes the dot product and ||v|| is the magnitude of v
# if the cosine is higher, the angles are closer together meaning the embeddings are more likely to be a match
def cosine_similarity(embedding1, embedding2):
    return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))

# runs InsightFace on an image to get a list of face data
def detect_image(filepath):
    # convert the image to cv2 so InsightFace can read it
    image = cv2.imread(filepath)
    # continue if the file type is valid
    if validate_path(filepath):
        faces = app.get(image)
    
        return image, faces or []
    else:
        print('This file is not supported by InsightFace')
        return image, []

# get a list of Pillow images of each face detected
def get_face_thumbnails(image, faces):
    face_thumbnails = []

    for face in faces:
        # bbox is the bounding box, this gets the location of the corners of the rectangle that contains the face
        x1, y1, x2, y2 = face.bbox.astype(int)
        # crop the cv2 image to isolate the face
        cropped_face = image[y1:y2, x1:x2]
        # recolor it since cv2 uses BGR and Pillow uses RGB
        cropped_face = cv2.cvtColor(cropped_face, cv2.COLOR_BGR2RGB)
        # turn the cv2 image into a Pillow image and resize it
        face_image = Image.fromarray(cropped_face)
        face_image.thumbnail((128, 128))
        # add it to the thumbnails list
        face_thumbnails.append(face_image)
    
    return face_thumbnails

# get a list of names that correspond to each face
def label_faces(face_embeddings):
    face_labels = []
    # get each face from the database
    saved_faces = database_manager.get_faces()
    # convert them back to vectors
    saved_faces = [(name, blob_to_embedding(embedding)) for name, embedding in saved_faces]

    # iterate through the faces detected in the image in the details ui
    for embedding1 in face_embeddings:
        # boolean to keep track of if the face has a name or not
        match_found = False

        # iterate through the faces saved on the database
        for face2 in saved_faces:
            name, embedding2 = face2
            # get the similiarity between the two embeddings
            similarity = cosine_similarity(embedding1, embedding2)
            # similarity > 0.5 means the faces are very likely to be a match
            if similarity > 0.5:
                face_labels.append(name)
                match_found = True

        # it's important to add None to the list so each label corresponds to the correct face
        # if faces = [embedding1, embedding2, embedding3] and face_labels = ["Alice", None, "Bob"]
        # then embedding1 has the name Alice and embedding3 has the name Bob while embedding2 has not been labelled yet by the user
        if not match_found:
            face_labels.append(None)
    
    return face_labels     

# convert an embedding (a tuple of floats) to bytes that can be stored in the database
def embedding_to_blob(embedding):
    return embedding.astype(np.float32).tobytes()

# convert data from the database back to an embedding
# the inverse of embedding_to_blob
def blob_to_embedding(embedding_as_blob):
    return np.frombuffer(embedding_as_blob, dtype=np.float32)
