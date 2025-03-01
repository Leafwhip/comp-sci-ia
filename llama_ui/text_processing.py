# import the library which allows the use of LLaMa3.2, a large language model
import ollama

# regex library used for processing LLaMa's output string
import re

def validate_path(filepath):
    # valid file extensions
    images = {'webp', 'dng', 'tif', 'tiff', 'mpo', 'jpg', 'bmp', 'heic', 'png', 'jpeg', 'pfm'}
    videos = {'mkv', 'ts', 'mp4', 'wmv', 'mpeg', 'asf', 'webm', 'avi', 'm4v', 'mpg', 'mov', 'gif'}

    # get the file extension of the filepath
    file_type = re.split(r'\.', filepath)[-1]
    
    # make sure the file extension is compatible with YOLO
    if file_type in images or file_type in videos:
        return True
    
    # if the file extension is invalid, YOLO won't run
    print('This file type is not supported')
    return False

# inputs a string to the large language model and returns its response
def input_llama(prompt):
    response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
    return response['message']['content']

# processes the user's text input and LLaMa's response
def process_input(input, valid_tags):
    # this is the string that will be inputted to LLaMa3.2
    # supposed to take the user's input which describes an image,
    # and choose the tags from valid_tags that would likely be detected in that image
    llama_request = f'Return a list of tags likely to be detected by the computer vision model YOLO11 in a picture described by the prompt below. Return your answer as a list separated by barriers | and surrrounded by square brackets. Return NOTHING except the list of tags.\nOnly use tags from this list: {valid_tags}.\nThe prompt is: {input}'
    
    # get LLaMa's response to the input
    output = input_llama(llama_request)
    print(llama_request)
    print(output)

    # process LLaMa's output to a usable list of tags
    # remove all whitespace
    output_tags = re.sub(r'[\r\n]', '', output)
    # get only the text within the square brackets []
    # the input to LLaMa requests that tags be surrounded by square brackets
    output_tags = re.match(r'\[.*\]', output_tags)[0]
    # gets a list of every tag in the list
    output_tags = re.findall(r'(\w+ *\w+)+', output_tags, re.IGNORECASE)
    # todo: error if no tags were generated
    print(output_tags)
    return output_tags

# finds the images with the most similar tags to LLaMa's, and returns their filepaths
def search(photos, request_tags, max_photos):
    # list that keeps track of the number of similar tags for each photo
    photo_scores = []

    # iterate through the photos list
    for photo_data in photos:
        # unpack the photo_data tuple
        (filepath, location, timestamp, photo_tags) = photo_data
        
        # count the number of tags the request_tags and photo_tags have in common
        # todo: get the location and timestamp, and factor that into the photo's score
        match_score = sum([tag in request_tags for tag in photo_tags])

        # add the result to photo_scores
        photo_scores.append((match_score, filepath))
        print(request_tags, photo_tags, match_score)
    
    # filters out photos with zero tags in common
    photo_scores = [photo for photo in photo_scores if photo[0] > 0]

    # don't display any images if none match
    # most likely, something went wrong with LLaMa's response
    if(len(photo_scores) == 0):
        print("No photos matched your search")
        return
    
    # sort the images by score and get the {max_photos} photos with the highest score
    photo_scores.sort(key=lambda x: x[0], reverse=True)
    best_photos = photo_scores[:max_photos]

    # map the list of (filepath, score) to only a list of filepaths
    photo_paths = [photo[1] for photo in best_photos]
    return photo_paths

