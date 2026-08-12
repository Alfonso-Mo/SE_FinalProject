import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.contrib.auth.decorators import login_required


@login_required
def home(request):

    nowplaying_url = "https://api.themoviedb.org/3/movie/now_playing"
    configuration_url = "https://api.themoviedb.org/3/configuration"

    headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {settings.TMDB_API_TOKEN}"
}

    movies = []

    # Get TMDB image configuration
    configuration_response = requests.get(
        configuration_url,
        headers=headers,
        timeout=10
    )

    # Get movies currently playing
    nowplaying_response = requests.get(
        nowplaying_url,
        headers=headers,
        params={
            "region": "US",
            "language": "en-US"
        },
        timeout=10
    )

    if (
        configuration_response.status_code == 200
        and nowplaying_response.status_code == 200
    ):

        configuration_data = configuration_response.json()
        nowplaying_data = nowplaying_response.json()

        base_url = configuration_data["images"]["secure_base_url"]
        poster_sizes = configuration_data["images"]["poster_sizes"]

        # Choose w500 if TMDB says it is available
        if "w500" in poster_sizes:
            poster_size = "w500"
        else:
            poster_size = poster_sizes[-1]

        for movie in nowplaying_data["results"]:

            # Keep only English-language movies if you still want that filter
            if movie["original_language"] != "en":
                continue

            if movie["poster_path"] is not None:
                movie["poster_url"] = (
                    base_url
                    + poster_size
                    + movie["poster_path"]
                )
            else:
                movie["poster_url"] = None

            movies.append(movie)

    return render(
        request,
        "movies/homepage.html",
        {"movies": movies}
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
    # redirect_authenticated_user = True


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("home")
