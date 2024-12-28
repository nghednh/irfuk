from pymongo import MongoClient
from transformers import pipeline
from image_search import load_index, get_movie_id_and_score, get_movie_id_and_score_from_file
from search import search_movies

MONGO_URI = "mongodb+srv://nghednh:123@cluster0.llhn1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['movie_db']
collection = db['movies']

def multimodal_search(query_text, query_img_url):

    image_index, image_urls = load_index()
    if image_index is None or image_urls is None:
        print("Image index or image URLs not found.")
        return []

    if not query_text and not query_img_url:
        print("Both text and image queries are empty.")
        return []
    text_results = []
    image_results = []

    if query_text:
        text_results = search_movies(query_text)
        print("\n--- Text-based search results ---")
        for movie_id, movie_name, score in text_results:
            print(f"Movie Name: {movie_name}, Score: {score}")

    if query_img_url:
        print(f"\nPerforming image search for query: {query_img_url}")
        image_results = get_movie_id_and_score(query_img_url, image_index, image_urls)  # Removed top_k argument
        print("\n--- Image-based search results ---")
        for movie_id, movie_name, score in image_results:
            print(f"Movie Name: {movie_name}, Score: {score}")
    combined_results = {}

    print("\n--- Processing Text Results ---")
    for movie_id, movie_name, score in text_results:
        combined_results[movie_name.lower()] = {
            "movie_id": movie_id,
            "name": movie_name,
            "text_score": score,
            "image_score": 0,
            "score": score
        }
        print(f"Added {movie_name} from text search with score {score}")

    print("\n--- Processing Image Results ---")
    for movie_id, movie_name, score in image_results:
        movie_key = movie_name.lower()
        if movie_key in combined_results:
            combined_results[movie_key]["image_score"] = score
            text_score = combined_results[movie_key]["text_score"]
            combined_results[movie_key]["score"] = (text_score *score)
            print(f"Updated {movie_name} with combined text and image scores")
        else:
            combined_results[movie_key] = {
                "movie_id": movie_id,
                "name": movie_name,
                "text_score": 0,
                "image_score": score,
                "score": score
            }
            print(f"Added {movie_name} from image search with score {score}")

    sorted_results = sorted(combined_results.values(), key=lambda x: x["score"], reverse=True)

    final_results = []
    print("\n--- Combined Results ---")
    for details in sorted_results:
        final_results.append({
            "movie_id": details["movie_id"],
            "movie_name": details["name"],
            "score": details["score"],
            "text_score": details["text_score"],
            "image_score": details["image_score"]
        })
        print(f"Movie Name: {details['name']}")
        print(f"- Text Score: {details['text_score']:.3f}")
        print(f"- Image Score: {details['image_score']:.3f}")
        print(f"- Final Score: {details['score']:.3f}\n")

    return final_results


def getIDmultimodal_search(query_text,query_img_url, image_index, image_urls):
    if image_index is None or image_urls is None:
        print("Image index or image URLs not found.")
        return []
    if not query_text and not query_img_url:
        print("Both text and image queries are empty.")
        return []

    text_results = []
    image_results = []
    if query_text:
        text_results = search_movies(query_text)
        if text_results:
            print("\n--- Text-based search results ---")
        else:
            print("No results found for text query.")
    if query_img_url:
        print(f"\nPerforming image search for query: {query_img_url}")
        image_results = get_movie_id_and_score(query_img_url, image_index, image_urls)
        if image_results:
            print("\n--- Image-based search results ---")
        else:
            print("No results found for image query.")
    combined_results = {}
    print("\n--- Processing Text Results ---")
    for movie_id, movie_name, score in text_results:
        if movie_name:
            combined_results[movie_name.lower()] = {
                "movie_id": movie_id,
                "name": movie_name,
                "text_score": score,
                "image_score": 0,
                "score": score * 0.6
            }


    print("\n--- Processing Image Results ---")
    for movie_id, movie_name, score in image_results:
        if movie_name:
            movie_key = movie_name.lower()
            if movie_key in combined_results:
                combined_results[movie_key]["image_score"] = score
                text_score = combined_results[movie_key]["text_score"]
                combined_results[movie_key]["score"] = (text_score * score)
                print(f"Updated {movie_name} with combined text and image scores")
            else:
                combined_results[movie_key] = {
                    "movie_id": movie_id,
                    "name": movie_name,
                    "text_score": 0,
                    "image_score": score,
                    "score": score
                }


    sorted_results = sorted(combined_results.values(), key=lambda x: x["score"], reverse=True)

    n = [details['movie_id'] for details in sorted_results]

    return n
def getIDmultimodal_search_from_file(query_text, image_path, image_index, image_urls):
    if image_index is None or image_urls is None:
        print("Image index or image URLs not found.")
        return []

    if not query_text and not image_path:
        print("Both text and image queries are empty.")
        return []

    text_results = []
    image_results = []

    # Process the text query if provided
    if query_text:
        text_results = search_movies(query_text)
        if text_results:
            print("\n--- Text-based search results ---")
        else:
            print("No results found for text query.")

    # Process the image query if provided (image from file)
    if image_path:
        print(f"\nPerforming image search for query: {image_path}")
        image_results = get_movie_id_and_score_from_file(image_path, image_index, image_urls)
        if image_results:
            print("\n--- Image-based search results ---")
        else:
            print("No results found for image query.")

    # Combine the results from both text and image searches
    combined_results = {}

    # Process the text-based search results
    print("\n--- Processing Text Results ---")
    for movie_id, movie_name, score in text_results:
        if movie_name:
            combined_results[movie_name.lower()] = {
                "movie_id": movie_id,
                "name": movie_name,
                "text_score": score,
                "image_score": 0,
                "score": score * 0.6  # Assign weight to text score
            }

    # Process the image-based search results
    print("\n--- Processing Image Results ---")
    for movie_id, movie_name, score in image_results:
        if movie_name:
            movie_key = movie_name.lower()
            if movie_key in combined_results:
                combined_results[movie_key]["image_score"] = score
                text_score = combined_results[movie_key]["text_score"]
                combined_results[movie_key]["score"] = (text_score * score)  # Combined score
                print(f"Updated {movie_name} with combined text and image scores")
            else:
                combined_results[movie_key] = {
                    "movie_id": movie_id,
                    "name": movie_name,
                    "text_score": 0,
                    "image_score": score,
                    "score": score
                }

    # Sort the combined results by the final score in descending order
    sorted_results = sorted(combined_results.values(), key=lambda x: x["score"], reverse=True)

    # Return a list of movie IDs based on the sorted results
    n = [details['movie_id'] for details in sorted_results]

    return n

if __name__ == "__main__":
    # Assuming the index and image URLs are already loaded
    index, image_urls = load_index()

    # Define the query text and image path
    query_text = "Moana"
    image_path = "ktykv512g7ld1.jpg"  # Provide the path to the image file

    # Perform the multimodal search
    movie_ids = getIDmultimodal_search_from_file(query_text, image_path, index, image_urls)

    # Print the results
    print("Top matching movie IDs:", movie_ids)

