# import the library which allows the use of LLaMa3.2, a large language model
import ollama

# regex library used for processing LLaMa's output string
import re

# used to get the current date for timestamp search
from datetime import datetime

# constants that adjust how score is calculated
LOCATION_FACTOR = 10
METADATA_STRICTNESS = 5
YEAR_FACTOR = 7
MONTH_FACTOR = 7
DAY_FACTOR = 7
MATCH_FACTOR = 7

# turns a location in the form Latitude(°N),Longitude(°E) to Latitude° N/S, Longitude° E/W
# used to display in image details
def location_to_readable(location):
    latitude, longitude = [float(n) for n in re.split(r',', location)]
    # find the direction letter to make the numbers positive and easier to read
    latitude_dir = 'S' if latitude < 0 else 'N'
    longitude_dir = 'W' if longitude < 0 else 'E' 
    
    return f'{latitude}°  {latitude_dir}, {longitude}°  {longitude_dir}'

# turns a timestamp in the form {year:month:day hours:minutes:seconds} to {month day, year hours:minutes AM/PM} 
# used to display in image details
def timestamp_to_readable(timestamp):
    # split the timestamp into date and time sections
    date, time = re.findall(r'[^ ]+', timestamp)

    # make the date readable and map the month from number to word
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    year, month, day = re.findall(r'\d+', date)
    readable_date = f'{months[int(month)-1]} {day}, {year}'

    # get the time and make it readable (using AM/PM instead of 24 hours)
    # seconds are ignored
    hours, minutes, seconds = [int(n) for n in re.findall(r'\d+', time)]
    pm_bool = False
    if hours > 12:
        pm_bool = True
        hours -= 12
    elif hours == 12:
        pm_bool = True
    elif hours == 0: 
        hours = 12
    readable_time = f'{hours}:{minutes} {"PM" if pm_bool else "AM"}'

    return f'{readable_date}  {readable_time}'

# inputs a string to the large language model and returns its response
def input_llama(prompt):
    response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
    return response['message']['content']

# processes the user's text input and LLaMa's response
def process_input(input, valid_tags, use_metadata):
    # this is the string that will be inputted to LLaMa3.2
    # supposed to take the user's input which describes an image,
    # and choose the tags from valid_tags that would likely be detected in that image
    llama_request = f'Return a list of tags (objects or people) likely to appear in an image described by the following input. Return your answer as a list surrounded by square brackets.\nOnly use tags from this list: {valid_tags}.\nThe input is: {input}'
    
    # get LLaMa's response to the input
    output_tags = input_llama(llama_request).lower()
    print(llama_request)
    print(output_tags)

    # process LLaMa's output to a usable list of tags
    # remove all whitespace
    output_tags = re.sub(r'[\r\n]', '', output_tags)
    # get only the text within the square brackets []
    # the input to LLaMa requests that tags be surrounded by square brackets
    output_tags = re.search(r'\[.*\]', output_tags)
    if output_tags:
        # gets a list of every tag in the list
        output_tags = re.findall(r'(\w+ *\w+)+', output_tags[0])
    else:
        # error if no tags were generated
        print('Error: no tags were generated for this request')

    print(output_tags)

    # runs two additional requests if metadata is toggled on
    if use_metadata:
        # request for LLaMa to guess the location the image was taken
        llama_location_request = f'Return approximate latitude and longitude coordinates where an image described by the input below might have been taken. The coordinates don\'t have to be exact but should be reasonably close to the location specified. Return the coordinates formatted like so: [Latitude (° N), Longitude (° E)].\nThe input is: {input}'
        output_location = input_llama(llama_location_request)
        print(llama_location_request)
        print(output_location)

        # request for LLaMa to guess the date the image was taken
        current_date = datetime.now().date()
        llama_timestamp_request = f'Return a likely date an image described by the input below might have been taken. Return the date in the form [YYYY:MM:DD] surrounded by square brackets. The current date is {current_date}.\nThe input is: {input}'
        output_timestamp = input_llama(llama_timestamp_request)
        print(llama_timestamp_request)
        print(output_timestamp)

        # regex to parse LLaMa's output
        output_location = re.sub(r'[\r\n]', '', output_location)
        output_location = re.search(r'\[.*\]', output_location)
        if output_location:
            output_location = re.findall(r'[\d\.]+', output_location[0])
            output_location = [float(n) for n in output_location]
            if len(output_location) != 2:
                output_location = None
        else:
            print('An error occured while generating the predicted location.')

        print(output_location)
        
        output_timestamp = re.sub(r'[\r\n]', '', output_timestamp)
        output_timestamp = re.search(r'\[.*\]', output_timestamp)
        if output_timestamp:
            output_timestamp = re.findall(r'\d+', output_timestamp[0])
            output_timestamp = [int(n) for n in output_timestamp]
            if len(output_timestamp) != 3:
                output_timestamp = None
        else:
            print('An error occured while generating the predicted timestamp.')

        print(output_timestamp)
        
        # if metadata is off or there was a problem generating location or timestamp
        # they will be returned as None
        return (output_tags, output_location, output_timestamp)
    
    return (output_tags, None, None)

# finds the images with the most similar tags to LLaMa's, and returns their filepaths
def search(photos, request_output, max_photos):
    # get all the request data
    request_tags, request_location, request_timestamp = request_output

    print(request_output)

    if request_location:
        request_latitude, request_longitude = request_location
    if request_timestamp:
        request_year, request_month, request_day = request_timestamp

    # list that keeps track of the number of similar tags for each photo
    photo_scores = []

    # iterate through the photos list
    for photo_data in photos:
        # get all the photo data
        filepath, folder_path, location, timestamp, photo_tags, photo_faces = photo_data
        print(filepath, location, timestamp, photo_tags)
        
        # score represents how strongly an image's data matches the request data
        # score from each section (location, timestamp, tags) is multiplied by a constant
        total_score = 0

        # calculate the score from location
        if location and request_location:
            latitude, longitude = [float(n) for n in re.split(r',', location)]
            # latitude and longitude are scored separately since LLaMa often misplaces a negative sign
            # score is calculated exponentially so only values close to the estimated result contribute meaningfully to the score
            latitude_score = METADATA_STRICTNESS ** -abs(latitude - request_latitude) * LOCATION_FACTOR
            longitude_score = METADATA_STRICTNESS ** -abs(longitude - request_longitude) * LOCATION_FACTOR
            total_score += latitude_score + longitude_score
            print(f'Latitude/longitude scores: {latitude_score}, {longitude_score}')
        
        # calculate the score from timestamp
        if timestamp and request_timestamp:
            date = re.search(r'[^ ]+', timestamp)[0]
            year, month, day = [int(n) for n in re.findall(r'\d+', date)]
            # timestamp score is calculated similarly to location
            year_score = METADATA_STRICTNESS ** -abs(year - request_year) * YEAR_FACTOR
            month_score = METADATA_STRICTNESS ** -abs(month - request_month) * MONTH_FACTOR
            day_score = METADATA_STRICTNESS ** -abs(day - request_day) * DAY_FACTOR
            total_score += year_score + month_score + day_score
            print(f'Year/month/day scores: {year_score}, {month_score}, {day_score}')
        

        # count the number of tags the request_tags and photo_tags have in common
        match_score = sum([tag in request_tags for tag in photo_tags]) * MATCH_FACTOR
        total_score += match_score

        # add the result to photo_scores
        photo_scores.append((total_score, filepath))
        print(f'Total score: {total_score}')
    
    # filters out photos with zero tags in common
    photo_scores = [photo for photo in photo_scores if photo[0] > 0]

    # don't display any images if none match
    # most likely, something went wrong with LLaMa's response
    if(len(photo_scores) == 0):
        print("No photos matched your search")
    
    # sort the images by score and get the {max_photos} photos with the highest score
    photo_scores.sort(key=lambda x: x[0], reverse=True)
    best_photos = photo_scores[:max_photos]

    # map the list of (filepath, score) to only a list of filepaths
    photo_paths = [photo[1] for photo in best_photos]
    return photo_paths

