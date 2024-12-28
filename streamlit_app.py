import streamlit as st
from multimodel import getIDmultimodal_search_from_file, getIDmultimodal_search  # Ensure correct import
from search import getID_search_movies
from image_search import getID_search_image_movie, getID_search_image_movie_from_file, load_index
import requests
from PIL import Image
import io
import numpy as np


def get_movie_details(movie_ids):
    api_key = '50767d9d58baff413d3f12803125ce4d'
    movie_details = []
    for movie_id in movie_ids:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            movie_details.append({
                "name": data.get("title"),
                "poster": f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}" if data.get('poster_path') else None,
                "overview": data.get("overview"),
                "release_date": data.get("release_date"),
                "rating": data.get("vote_average"),
                "genres": ", ".join([genre['name'] for genre in data.get('genres', [])])
            })
    return movie_details


# Function to display movie details
def display_movie_details(movie_details):
    for movie in movie_details:
        with st.container():
            st.markdown("---")
            col1, col2 = st.columns([1, 3])

            with col1:
                if movie['poster']:
                    st.image(movie['poster'], width=200)
                else:
                    st.write("Poster not found")

            with col2:
                st.subheader(movie['name'])
                st.write(f"**Release Date:** {movie['release_date']}")
                st.write(f"**Rating:** {movie['rating']} 🌟")
                st.write(f"**Genres:** {movie['genres']}")
                st.write(f"**Overview:** {movie['overview']}")

# Streamlit UI
st.title("Movie Search")
st.write("Search for movies using text, image, or multimodal input.")


@st.cache_resource
def load_index_once():
    return load_index()


index, image_urls = load_index_once()

tab_selection = st.radio("Select search method", ("Text Search", "Image Search", "Multimodal Search"))

if tab_selection == "Text Search":
    query = st.text_input("Enter movie name (e.g., 'Red One')")
    if query:
        movie_ids = getID_search_movies(query)
        # st.write("Found movie IDs:", movie_ids)
        if movie_ids:
            movie_details = get_movie_details(movie_ids)
            display_movie_details(movie_details)

elif tab_selection == "Image Search":
    image_option = st.radio("Choose how to provide the image", ("Upload Image", "Paste Image URL"))

    if image_option == "Upload Image":
        uploaded_image = st.file_uploader("Upload an image file", type=["jpg", "jpeg", "png"])

        if uploaded_image:
            image = Image.open(uploaded_image)
            st.image(image, caption="Uploaded Image", use_container_width=True)

            movie_ids = getID_search_image_movie_from_file(uploaded_image, index, image_urls)
            st.write("Found movie IDs:", movie_ids)
            if movie_ids:
                movie_details = get_movie_details(movie_ids)
                display_movie_details(movie_details)

    elif image_option == "Paste Image URL":
        img_url = st.text_input("Enter image URL")
        if img_url:
            response = requests.get(img_url)
            if response.status_code == 200:
                url_image = Image.open(io.BytesIO(response.content))
                st.image(url_image, caption="Image from URL", use_container_width=True)

                movie_ids = getID_search_image_movie(img_url, index, image_urls)
                st.write("Found movie IDs:", movie_ids)
                if movie_ids:
                    movie_details = get_movie_details(movie_ids)
                    display_movie_details(movie_details)

elif tab_selection == "Multimodal Search":
    image_option = st.radio("Choose how to provide the image", ("Upload Image", "Paste Image URL"))
    query = st.text_input("Enter movie name (e.g., 'Moana')")

    if image_option == "Upload Image":
        uploaded_image = st.file_uploader("Upload an image file", type=["jpg", "jpeg", "png"])

        if uploaded_image:
            image = Image.open(uploaded_image)
            st.image(image, caption="Uploaded Image", use_container_width=True)

            movie_ids = getIDmultimodal_search_from_file(query, uploaded_image, index, image_urls)
            st.write("Found movie IDs:", movie_ids)
            if movie_ids:
                movie_details = get_movie_details(movie_ids)
                display_movie_details(movie_details)

    elif image_option == "Paste Image URL":
        img_url = st.text_input("Enter image URL")
        if img_url:
            response = requests.get(img_url)
            if response.status_code == 200:
                url_image = Image.open(io.BytesIO(response.content))
                st.image(url_image, caption="Image from URL", use_container_width=True)

                movie_ids = getIDmultimodal_search(query, img_url, index, image_urls)
                st.write("Found movie IDs:", movie_ids)
                if movie_ids:
                    movie_details = get_movie_details(movie_ids)
                    display_movie_details(movie_details)
