import requests

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View


@login_required
def home(request):
    # 1. Check if there is a search query in the URL
    search_query = request.GET.get('q')

    nowplaying_url = "https://api.themoviedb.org/3/movie/now_playing"
    search_url = "https://api.themoviedb.org/3/search/movie"
    configuration_url = "https://api.themoviedb.org/3/configuration"

    # HARDCODED TMDB TOKEN
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIwNTQyMTUxNjgyZTE5YzAzZmJlNjM5MDM5ZDkwZDhlOSIsIm5iZiI6MTc4NjQyMTY0NS4zODcsInN1YiI6IjZhN2FhMThkZDc0NzllOTk5YWY4ZWY1YiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.zc0YCmg5qv4Qp5NQtYyuv2vVqMiMrIm7rNboKxhHU9I"
    }

    movies = []

    # Get TMDB image configuration
    configuration_response = requests.get(
        configuration_url,
        headers=headers,
        timeout=10
    )

    # 2. If the user searched, use the Search API. Otherwise, get Now Playing.
    if search_query:
        movies_response = requests.get(
            search_url,
            headers=headers,
            params={
                "query": search_query,
                "language": "en-US",
                "page": 1,
                "include_adult": "false"
            },
            timeout=10
        )
    else:
        movies_response = requests.get(
            nowplaying_url,
            headers=headers,
            params={
                "region": "US",
                "language": "en-US",
                "page": 1
            },
            timeout=10
        )

    if (
        configuration_response.status_code == 200
        and movies_response.status_code == 200
    ):

        configuration_data = configuration_response.json()
        movies_data = movies_response.json()

        base_url = configuration_data["images"]["secure_base_url"]
        poster_sizes = configuration_data["images"]["poster_sizes"]

        # Choose w500 if TMDB says it is available
        if "w500" in poster_sizes:
            poster_size = "w500"
        else:
            poster_size = poster_sizes[-1]

        for movie in movies_data.get("results", []):
            
            # Keep only English-language movies
            if movie.get("original_language") != "en":
                continue

            if movie.get("poster_path"):
                movie["poster_url"] = (
                    base_url
                    + poster_size
                    + movie.get("poster_path")
                )
            else:
                movie["poster_url"] = None

            movies.append(movie)

    # 3. Pass the search_query back to the template so we can display it
    return render(
        request,
        "movies/homepage.html",
        {
            "movies": movies,
            "search_query": search_query
        }
    )


class SignUpView(View):
    template_name = "movies/signup.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("home")
        form = UserCreationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("home")
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
        return render(request, self.template_name, {"form": form})


class UserLoginView(LoginView):
    template_name = "movies/login.html"


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("home")


# --- WATCH TRAILER FEATURE ---

@login_required
def movie_detail(request, movie_id):
    movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    videos_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos"
    
    # HARDCODED TMDB TOKEN
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIwNTQyMTUxNjgyZTE5YzAzZmJlNjM5MDM5ZDkwZDhlOSIsIm5iZiI6MTc4NjQyMTY0NS4zODcsInN1YiI6IjZhN2FhMThkZDc0NzllOTk5YWY4ZWY1YiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.zc0YCmg5qv4Qp5NQtYyuv2vVqMiMrIm7rNboKxhHU9I"
    }
    
    # 1. Fetch specific movie details
    movie_response = requests.get(movie_url, headers=headers, timeout=10)
    movie_data = movie_response.json() if movie_response.status_code == 200 else {}
    
    # 2. Fetch the movie's videos (Trailers)
    videos_response = requests.get(videos_url, headers=headers, timeout=10)
    
    # 3. Find the YouTube trailer key
    trailer_key = None
    if videos_response.status_code == 200:
        videos_data = videos_response.json()
        for video in videos_data.get('results', []):
            if video.get('site') == 'YouTube' and video.get('type') == 'Trailer':
                trailer_key = video.get('key')
                break
            
    context = {
        'movie': movie_data,
        'trailer_key': trailer_key
    }
    return render(request, 'movies/movie_detail.html', context) #added code from codespace so we can search 