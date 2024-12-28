import requests
from pymongo import MongoClient
MONGO_URI = "mongodb+srv://nghednh:123@cluster0.llhn1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['movie_db']
collection = db['movies']

API_KEY = '50767d9d58baff413d3f12803125ce4d'
BASE_URL = "https://api.themoviedb.org/3/movie/"
def get_movie_data(movie_id):
    print(f"Fetching data for movie ID: {movie_id}")
    url = f"{BASE_URL}{movie_id}?api_key={API_KEY}&language=en-US"
    response = requests.get(url).json()

    if 'status_code' in response and response['status_code'] == 34:
        print(f"Movie ID {movie_id} not found in TMDb.")
        return None

    movie_data = {
        'movie_id': movie_id,
        'name': response.get('original_title'),
        'overview': response.get('overview'),
        'subtitle': response.get('tagline'),
        'images': get_movie_images(movie_id)
    }
    return movie_data

def get_movie_images(movie_id):
    print(f"Fetching images for movie ID: {movie_id}")
    url = f"{BASE_URL}{movie_id}/images?api_key={API_KEY}"
    response = requests.get(url).json()
    images = []
    for img in response.get('posters', []):
        images.append(f"https://image.tmdb.org/t/p/w500{img['file_path']}")
    return images

def crawl_movies(movie_ids):
    print("Starting to crawl movies.")
    for movie_id in movie_ids:
        print(f"Crawling movie ID: {movie_id}")
        movie_data = get_movie_data(movie_id)
        if movie_data:
            collection.update_one({'movie_id': movie_id}, {'$set': movie_data}, upsert=True)
            movie_in_db = collection.find_one({'movie_id': movie_id})
            if movie_in_db:
                print(f"Movie data for ID {movie_id} successfully saved to DB: {movie_in_db}")
            else:
                print(f"Failed to save movie data for ID {movie_id} to DB.")
        else:
            print(f"Skipping movie ID {movie_id}.")
def print_movies_from_db():
    print("Movies stored in the database:")
    movies = collection.find()
    for movie in movies:
        print(f"Movie ID: {movie.get('movie_id')}")
        print(f"Name: {movie.get('name')}")
        print(f"Overview: {movie.get('overview')}")
        print(f"Subtitle: {movie.get('subtitle')}")
        #print(f"Images: {movie.get('images')}")
        print("-" * 50)

def get_popular_movies(language, page_x, page_y):
    print(f"Fetching popular movies in {language} between pages {page_x} and {page_y}.")
    for page in range(page_x, page_y + 1):
        print(f"Fetching page {page} for language {language}...")
        url = (
            f"https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}"
            f"&language={language}&page={page}"
        )
        response = requests.get(url).json()
        if 'status_code' in response and response['status_code'] != 200:
            print(f"Error fetching movies on page {page}. Response: {response}")
            break
        movie_ids = [movie['id'] for movie in response.get('results', [])]
        if not movie_ids:
            print(f"No movies found on page {page} for language {language}.")
            break
        crawl_movies(movie_ids)
    print(f"Completed fetching popular movies in {language} from pages {page_x} to {page_y}.")
page_start = 1
page_end = 200
get_popular_movies(language="en-US", page_x=page_start, page_y=page_end)
get_popular_movies(language="vi-VN", page_x=page_start, page_y=page_end)
print_movies_from_db()
document_count = collection.count_documents({})
print(f"Number of documents in the 'movies' collection: {document_count}")



