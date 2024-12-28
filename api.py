import streamlit as st
import requests

# TMDb API details
API_KEY = "50767d9d58baff413d3f12803125ce4d"
BASE_URL = "https://api.themoviedb.org/3/movie/"

def get_movie_info_by_id(movie_id):
    url = f"{BASE_URL}{movie_id}?api_key={API_KEY}&language=en-US"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Example movie ID (replace with actual movie ID)
movie_id = 550 # Example ID for "Fight Club"

movie_info = get_movie_info_by_id(movie_id)
if movie_info:
    poster_url = f"https://image.tmdb.org/t/p/w500{movie_info['poster_path']}" if movie_info['poster_path'] else None
    release_date = movie_info['release_date']
    rating = movie_info['vote_average']
    genres = ", ".join([genre['name'] for genre in movie_info['genres']])
    overview = movie_info['overview']

    with st.container():
        st.markdown("---")
        col1, col2 = st.columns([1, 3])

        with col1:
            if poster_url:
                st.image(poster_url, width=200)
            else:
                st.write("Poster not found")

        with col2:
            st.subheader(movie_info['title'])
            st.write(f"**Release Date:** {release_date}")
            st.write(f"**Rating:** {rating} 🌟")
            st.write(f"**Genres:** {genres}")
            st.write(f"**Overview:** {overview}")
else:
    st.write("Movie not found.")
