from math import radians, sin, cos, sqrt, atan2
import requests, json, openai

def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3  # Earth's radius in meters
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    d = R * c
    return d

#####################################################################################################
# Set the API key and endpoint
api_key = 'Google_Maps_API_Key'
endpoint = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
details_endpoint = 'https://maps.googleapis.com/maps/api/place/details/json'
# Set the headers
headers = {
    'Authorization': 'Bearer %s' % api_key,
}
#####################################################################################################
# Set the user's location
# Example:
latitude = 24.694900
longitude = 46.724100
#####################################################################################################
# Set the types of places to search for
types = ['restaurant', 'cafe', 'store', 'supermarket','mosque']
#####################################################################################################
# Create a dictionary to store the results for each type
results_dict = {}
#####################################################################################################
# Initialize OpenAI client
openai_api_key = 'ChatGPT_API_Key'
openai_model = 'text-davinci-002'
openai.api_key = openai_api_key
#####################################################################################################
# Loop through the types of places
for place_type in types:
    # Set the parameters
    parameters = {
        'location': f'{latitude},{longitude}',
        'radius': 500,   # 500 Meters
        'type': place_type,
        'key': api_key,
    }

    #Send the request to the Google Places API
    response = requests.get(url=endpoint, params=parameters)

    # Get the response data
    data = response.json()

    # Get the list of results
    results = data['results']

    # Create a list to store the information about each result
    result_info = []

    # Loop through the results
    for result in results:
        # Get the information about the result
        name = result['name']
        rating = result.get('rating', 0)
        distance = round(haversine(latitude,longitude,result['geometry']['location']['lat'],result['geometry']['location']['lng']))
        image_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={result['photos'][0]['photo_reference']}&key={api_key}" if 'photos' in result else None
        place_id = result['place_id']
        google_maps_url = f'https://www.google.com/maps/place/?q=place_id:{place_id}'
        
        # Get place_id to get reviews from details endpoint
        place_id = result['place_id']
        
        # Set details parameters
        details_parameters = {
            'place_id': place_id,
            'fields': 'review',
            'key': api_key,
        }
        
        # Send request to details endpoint to get reviews
        details_response = requests.get(url=details_endpoint, params=details_parameters)
        
        # Get details response data
        details_data = details_response.json()
        
        # Get all available reviews from details data and concatenate them into a single string separated by '-'
        reviews_list = details_data.get('result', {}).get('reviews', [])
        review_text_list = [review.get('text', '') for review in reviews_list]
        review_text_string = '-'.join(review_text_list)
        
        # Use OpenAI API to generate summary of advantages and disadvantages of reviews (The Prompt)
        prompt = f'Here are the reviews: {review_text_string}. Summarize the following reviews in the form "Advantages: Example - Example ... \\n Disadvantages: Example - Example ..." Make sure you write useful, brief and real things. Also above them all write a small overview like this:"Overview: Example example example...etc" less than 10 words about the place that these reviews were for which is {name} and make sure your answers are useful. Then write the advantages and disadvantages. Dont write the same advantage or disadvantage more than one time. Dont write anything other than Overview, Advantages and Disadvantages except for mosques where you should only write Overview and Advantages only.'
        
        openai_response = openai.Completion.create(
                                                engine=openai_model,
                                                prompt=prompt,
                                                max_tokens=100,
                                                temperature=0.5,
                                                n=1,
                                                stop=None)
        
        openai_text_string = openai_response['choices'][0]['text'].strip()

        # Store the information in a dictionary
        info = {
            'name': name,
            'rating': rating,
            'distance': distance,
            'image_url': image_url,
            'google_maps_url': google_maps_url,
            'review': openai_text_string,
        }


        # Add the dictionary to the list
        result_info.append(info)

    # Sort Places based on Rating
    result_info = sorted(result_info, key=lambda x: x['rating'], reverse=True)
    
    # Store the list of result information in the dictionary
    results_dict[place_type] = result_info

# Print the dictionary of results
print(json.dumps(results_dict, indent=2))
