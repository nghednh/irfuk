

import os
import faiss
import numpy as np
import requests
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.applications import ResNet50
from pymongo import MongoClient
import pickle
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

MONGO_URI = "mongodb+srv://nghednh:123@cluster0.llhn1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['movie_db']
collection = db['movies']

# Initialize the ResNet50 model for image feature extraction
model = ResNet50(weights='imagenet', include_top=False, pooling='avg')

IMAGE_INDEX_FOLDER = "image_index"
INDEX_FILE = os.path.join(IMAGE_INDEX_FOLDER, "movie_image_index.index")
IMAGE_URLS_FILE = os.path.join(IMAGE_INDEX_FOLDER, "image_urls.pkl")

if not os.path.exists(IMAGE_INDEX_FOLDER):
    os.makedirs(IMAGE_INDEX_FOLDER)

def extract_image_embedding(img_url):
    try:
        response = requests.get(img_url)
        img = image.load_img(BytesIO(response.content), target_size=(224, 224))  # BytesIO used here
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        embedding = model.predict(img_array)
        return embedding.flatten()
    except Exception as e:
        print(f"Error processing image {img_url}: {e}")
        return np.zeros((model.output_shape[-1],))

def process_images_concurrently(image_urls):
    with ThreadPoolExecutor(max_workers=8) as executor:
        embeddings = list(executor.map(extract_image_embedding, image_urls))
    return np.array(embeddings)

def batch_process_images(image_urls, batch_size=10):
    all_embeddings = []
    for i in range(0, len(image_urls), batch_size):
        batch = image_urls[i:i + batch_size]
        batch_embeddings = process_images_concurrently(batch)
        all_embeddings.append(batch_embeddings)
    return np.vstack(all_embeddings)
def index_images():
    image_urls = []
    processed_count = 0
    index, existing_image_urls = load_index()
    if index is None or existing_image_urls is None:
        print("No existing index or image URLs, starting fresh.")

    existing_image_urls_set = set(existing_image_urls) if existing_image_urls else set()

    while True:
        for movie in collection.find().limit(20):
            start_index = processed_count * 10000
            end_index = start_index + 10000
            batch_urls = movie['images'][start_index:end_index]

            image_urls_for_movie = []

            for img_url in batch_urls:
                if img_url not in existing_image_urls_set:
                    image_urls_for_movie.append(img_url)

            if image_urls_for_movie:
                image_urls.extend(image_urls_for_movie)

        if not image_urls:
            user_input = input(
                "No new images to process. Do you want to continue with the next batch? (yes/no): ").strip().lower()
            if user_input not in ["yes", "y"]:
                print("Batch processing stopped by user.")
                break
            else:
                processed_count += 1
                continue

        image_embeddings = batch_process_images(image_urls)

        if index is None:
            index = faiss.IndexFlatL2(image_embeddings.shape[1])

        index.add(image_embeddings)

        faiss.write_index(index, INDEX_FILE)

        all_image_urls = (existing_image_urls if existing_image_urls else []) + image_urls

        with open(IMAGE_URLS_FILE, "wb") as f:
            pickle.dump(all_image_urls, f)

        print(f"Processed batch {processed_count + 1}: {len(image_urls)} images indexed.")
        user_input = input("Continue with the next batch? (yes/no): ").strip().lower()
        if user_input not in ["yes", "y"]:
            print("Batch processing stopped by user.")
            break

        processed_count += 1
        image_urls = []

def load_index():
    if not os.path.exists(INDEX_FILE) or not os.path.exists(IMAGE_URLS_FILE):
        return None, None

    index = faiss.read_index(INDEX_FILE)

    with open(IMAGE_URLS_FILE, "rb") as f:
        image_urls = pickle.load(f)

    return index, image_urls

def search_similar_image(query_img_url, index, top_k=10):
    query_embedding = extract_image_embedding(query_img_url)
    query_embedding = np.array([query_embedding])

    D, I = index.search(query_embedding, k=top_k)
    return I[0], D[0]
def get_movies_from_image_urls(image_urls):
    movie_docs = []
    for img_url in image_urls:
        movie = collection.find_one({"images": img_url})
        if movie:
            movie_docs.append(movie)
    return movie_docs


def get_movie_id_and_score(query_img_url, index, image_urls, top_k=10):
    similar_image_indices, distances = search_similar_image(query_img_url, index, top_k)

    if similar_image_indices.size == 0 or distances.size == 0:
        print("No similar images found.")
        return []

    similar_image_urls = [image_urls[idx] for idx in similar_image_indices]
    similar_movies = get_movies_from_image_urls(similar_image_urls)
    seen_movie_ids = set()
    seen_movie_names = set()
    movie_scores = []

    for movie, distance in zip(similar_movies, distances):
        movie_id = movie.get('movie_id', 'Unknown ID')
        movie_name = movie.get('name', 'Unknown')

        if movie_id not in seen_movie_ids and movie_name not in seen_movie_names:

            seen_movie_ids.add(movie_id)
            seen_movie_names.add(movie_name)
            movie_scores.append((movie_id, movie_name, distance))

    movie_scores.sort(key=lambda x: x[2], reverse=True)

    return movie_scores



def getID_search_image_movie(query_img_url, index, image_urls, top_k=10):
    similar_image_indices, distances = search_similar_image(query_img_url, index, top_k)

    if similar_image_indices.size == 0 or distances.size == 0:
        print("No similar images found.")
        return []
    similar_image_urls = [image_urls[idx] for idx in similar_image_indices]
    similar_movies = get_movies_from_image_urls(similar_image_urls)
    seen_movie_ids = set()
    seen_movie_names = set()
    movie_ids = []

    for movie, distance in zip(similar_movies, distances):
        movie_id = movie.get('movie_id', 'Unknown ID')
        movie_name = movie.get('name', 'Unknown')
        if movie_id not in seen_movie_ids and movie_name not in seen_movie_names:
            seen_movie_ids.add(movie_id)
            seen_movie_names.add(movie_name)
            movie_ids.append(movie_id)

    return movie_ids
def getID_search_image_movie(query_img_url, index, image_urls, top_k=10):
    similar_image_indices, distances = search_similar_image(query_img_url, index, top_k)

    if similar_image_indices.size == 0 or distances.size == 0:
        print("No similar images found.")
        return []
    similar_image_urls = [image_urls[idx] for idx in similar_image_indices]
    similar_movies = get_movies_from_image_urls(similar_image_urls)
    seen_movie_ids = set()
    seen_movie_names = set()
    movie_ids = []

    for movie, distance in zip(similar_movies, distances):
        movie_id = movie.get('movie_id', 'Unknown ID')
        movie_name = movie.get('name', 'Unknown')
        if movie_id not in seen_movie_ids and movie_name not in seen_movie_names:
            seen_movie_ids.add(movie_id)
            seen_movie_names.add(movie_name)
            movie_ids.append(movie_id)

    return movie_ids

def extract_image_embedding_from_file(image_path):
    try:
        # Load image from file
        img = image.load_img(image_path, target_size=(224, 224))  # Resize to ResNet input size
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)

        # Extract embedding using the ResNet50 model
        embedding = model.predict(img_array)
        return embedding.flatten()
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return np.zeros((model.output_shape[-1],))  # Return a zero embedding in case of error


def search_similar_image_from_file(image_path, index, top_k=10):
    # Extract embedding for the query image
    query_embedding = extract_image_embedding_from_file(image_path)
    query_embedding = np.array([query_embedding])

    # Perform the search
    D, I = index.search(query_embedding, k=top_k)
    return I[0], D[0]
def getID_search_image_movie_from_file(image_path, index, image_urls, top_k=10):
    similar_image_indices, distances = search_similar_image_from_file(image_path, index, top_k)

    if similar_image_indices.size == 0 or distances.size == 0:
        print("No similar images found.")
        return []

    # Get the URLs of the most similar images
    similar_image_urls = [image_urls[idx] for idx in similar_image_indices]

    # Retrieve the corresponding movies
    similar_movies = get_movies_from_image_urls(similar_image_urls)

    seen_movie_ids = set()
    seen_movie_names = set()
    movie_ids = []

    for movie, distance in zip(similar_movies, distances):
        movie_id = movie.get('movie_id', 'Unknown ID')
        movie_name = movie.get('name', 'Unknown')
        if movie_id not in seen_movie_ids and movie_name not in seen_movie_names:
            seen_movie_ids.add(movie_id)
            seen_movie_names.add(movie_name)
            movie_ids.append(movie_id)

    return movie_ids
def get_movie_id_and_score_from_file(image_path, index, image_urls, top_k=10):
    # Step 1: Get similar image indices and distances
    similar_image_indices, distances = search_similar_image_from_file(image_path, index, top_k)

    # Step 2: If no similar images were found, return an empty list
    if similar_image_indices.size == 0 or distances.size == 0:
        print("No similar images found.")
        return []

    # Step 3: Get the image URLs of the most similar images
    similar_image_urls = [image_urls[idx] for idx in similar_image_indices]

    # Step 4: Retrieve the corresponding movies using the image URLs
    similar_movies = get_movies_from_image_urls(similar_image_urls)

    # Step 5: Avoid duplicate movies based on movie ID and name
    seen_movie_ids = set()
    seen_movie_names = set()
    movie_scores = []

    for movie, distance in zip(similar_movies, distances):
        movie_id = movie.get('movie_id', 'Unknown ID')
        movie_name = movie.get('name', 'Unknown')

        # Ensure no duplicate entries based on movie ID and name
        if movie_id not in seen_movie_ids and movie_name not in seen_movie_names:
            seen_movie_ids.add(movie_id)
            seen_movie_names.add(movie_name)
            movie_scores.append((movie_id, movie_name, distance))

    # Step 6: Sort the results by distance (lower distance means more similar)
    movie_scores.sort(key=lambda x: x[2], reverse=True)

    # Step 7: Return the sorted list of movie IDs, names, and distances (scores)
    return movie_scores

if __name__ == "__main__":
    image_path = "ktykv512g7ld1.jpg"  # Provide the path to the image file
    index, image_urls = load_index()

    if index is None or image_urls is None:
        print("Error: Index or image URLs could not be loaded. Exiting.")
    else:
        movie_scores = get_movie_id_and_score_from_file(image_path, index, image_urls)
        for movie_score in movie_scores:
            print(f"Movie ID: {movie_score[0]}, Movie Name: {movie_score[1]}, Score: {movie_score[2]}")
