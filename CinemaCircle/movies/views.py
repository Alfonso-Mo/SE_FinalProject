import requests
from django.shortcuts import render

def home(request):
    # Your TMDB API key 
    api_key = '0542151682e19c03fbe639039d90d8e9'
    
    # The TMDB endpoint for movies currently playing in theaters
    url = f"https://api.themoviedb.org/3/movie/now_playing?api_key={api_key}&language=en-US&page=1"
    
    # Makes the request to TMDB and convert the response to a Python dictionary
    response = requests.get(url)
    data = response.json()
    
    # Extract just the list of movies
    movies = data.get('results', [])
    
    # Sends the movie list to your home.html template
    return render(request, 'movies/home.html', {'movies': movies})