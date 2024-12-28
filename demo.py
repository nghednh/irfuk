from multimodel import getIDmultimodal_search
from search import getID_search_movies
from image_search import load_index, getID_search_image_movie

index, image_urls = load_index()
movie_ids = getID_search_movies("Red one")
print(movie_ids)
# put in img link

movie_ids2 = getID_search_image_movie("https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcRc35OBsYaT5o0GrpVKw3ueXDTnbpq5GRdaaSlyl_erdCLA9NE2",index, image_urls)
print(movie_ids2)
movie_ids3 = getIDmultimodal_search("Moana",index, image_urls, "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcRc35OBsYaT5o0GrpVKw3ueXDTnbpq5GRdaaSlyl_erdCLA9NE2")
print(movie_ids3)