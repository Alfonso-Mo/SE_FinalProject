import requests
from django.shortcuts import render

def home(request):
    # Your TMDB API key 
    api_key = '0542151682e19c03fbe639039d90d8e9'
    
    # Fetch Now Playing movies
    url = f"https://api.themoviedb.org/3/movie/now_playing?api_key={api_key}&language=en-US&page=1"
    response = requests.get(url)
    data = response.json()
    movies = data.get('results', [])
    
    return render(request, 'movies/home.html', {'movies': movies})

def movie_detail(request, movie_id):
    # Your TMDB API key 
    api_key = '0542151682e19c03fbe639039d90d8e9'
    
    # 1. Fetch specific movie details
    movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    movie_data = requests.get(movie_url).json()
    
    # 2. Fetch the movie's videos (Trailers)
    videos_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={api_key}&language=en-US"
    videos_data = requests.get(videos_url).json()
    
    # 3. Find the YouTube trailer key
    trailer_key = None
    for video in videos_data.get('results', []):
        if video.get('site') == 'YouTube' and video.get('type') == 'Trailer':
            trailer_key = video.get('key')
            break
            
    context = {
        'movie': movie_data,
        'trailer_key': trailer_key
    }
    return render(request, 'movies/movie_detail.html', context)