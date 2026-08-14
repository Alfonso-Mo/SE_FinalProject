from datetime import datetime

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Avg, Count, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST

from .forms import CommentForm, MovieScoresForm
from .models import Comment, CommentVote, Movie, Rating, WorthWatching



def _tmdb_headers():
    token = settings.TMDB_API_TOKEN
    if not token:
        return {"accept": "application/json"}
    return {
        "accept": "application/json",
        "Authorization": f"Bearer {token}",
    }


def _fetch_tmdb_movie(movie_id):
    movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    response = requests.get(movie_url, headers=_tmdb_headers(), timeout=10)
    if response.status_code != 200:
        return {}
    return response.json()


def _poster_url_from_path(poster_path):
    if not poster_path:
        return ""
    return f"https://image.tmdb.org/t/p/w500{poster_path}"


def _parse_release_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def upsert_movie_from_tmdb(movie_id, movie_data=None):
    if movie_data is None:
        movie_data = _fetch_tmdb_movie(movie_id)
    if not movie_data or not movie_data.get("id"):
        raise Http404("Movie not found")

    api_id = str(movie_data["id"])
    defaults = {
        "title": movie_data.get("title") or f"Movie {api_id}",
        "overview": movie_data.get("overview") or "",
        "poster_url": _poster_url_from_path(movie_data.get("poster_path")),
        "release_date": _parse_release_date(movie_data.get("release_date")),
    }
    movie, _created = Movie.objects.update_or_create(
        api_id=api_id,
        defaults=defaults,
    )
    return movie, movie_data


def build_comment_tree(comments, user):
    by_parent = {}
    user_votes = {}
    if user.is_authenticated:
        user_votes = {
            vote.comment_id: vote.value
            for vote in CommentVote.objects.filter(
                user=user,
                comment_id__in=[c.id for c in comments],
            )
        }

    nodes = []
    for comment in comments:
        comment.user_vote = user_votes.get(comment.id)
        comment.child_nodes = []
        nodes.append(comment)
        by_parent.setdefault(comment.parent_id, []).append(comment)

    for comment in nodes:
        comment.child_nodes = by_parent.get(comment.id, [])

    return by_parent.get(None, [])


def fetch_now_playing_movies(search_query=None):
    nowplaying_url = "https://api.themoviedb.org/3/movie/now_playing"
    search_url = "https://api.themoviedb.org/3/search/movie"
    configuration_url = "https://api.themoviedb.org/3/configuration"
    
    headers = _tmdb_headers()
    movies = []

    configuration_response = requests.get(
        configuration_url,
        headers=headers,
        timeout=10,
    )


    if search_query:
        movies_response = requests.get(
            search_url,
            headers=headers,
            params={
                "query": search_query,
                "language": "en-US",
                "page": 1,
                "include_adult": "false",
            },
            timeout=10,
        )
    else:
        movies_response = requests.get(
            nowplaying_url,
            headers=headers,
            params={
                "region": "US",
                "language": "en-US",
                "page": 1,
            },
            timeout=10,
        )


    if (
        configuration_response.status_code == 200
        and movies_response.status_code == 200
    ):
        configuration_data = configuration_response.json()
        movies_data = movies_response.json()

        base_url = configuration_data["images"]["secure_base_url"]
        poster_sizes = configuration_data["images"]["poster_sizes"]
        poster_size = "w500" if "w500" in poster_sizes else poster_sizes[-1]

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

    return movies


@login_required
def home(request):
    search_query = request.GET.get("q", "").strip()

    movies = fetch_now_playing_movies(
        search_query if search_query else None
    )

    return render(
        request,
        "movies/homepage.html",
        {
            "movies": movies,
            "search_query": search_query,
        },
    )


@login_required
def discussions_list(request):
    movies = fetch_now_playing_movies()

    api_ids = [str(movie["id"]) for movie in movies]

    comment_counts = {
        row["api_id"]: row["comment_total"]
        for row in Movie.objects.filter(api_id__in=api_ids)
        .annotate(comment_total=Count("comments"))
        .values("api_id", "comment_total")
    }

    for movie in movies:
        movie["comment_count"] = comment_counts.get(
            str(movie["id"]),
            0
        )

    return render(
        request,
        "movies/discussions_list.html",
        {"movies": movies},
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
    db_movie, movie_data = upsert_movie_from_tmdb(movie_id)

    if request.method == "POST":
        form = MovieScoresForm(request.POST)
        if form.is_valid():
            Rating.objects.update_or_create(
                user=request.user,
                movie=db_movie,
                defaults={"score": form.cleaned_data["rating"]},
            )
            WorthWatching.objects.update_or_create(
                user=request.user,
                movie=db_movie,
                defaults={"score": form.cleaned_data["worth_watching"]},
            )
            return redirect("movie_detail", movie_id=movie_id)
    else:
        existing_rating = Rating.objects.filter(
            user=request.user,
            movie=db_movie,
        ).first()
        existing_worth = WorthWatching.objects.filter(
            user=request.user,
            movie=db_movie,
        ).first()
        initial = {}
        if existing_rating:
            initial["rating"] = existing_rating.score
        if existing_worth:
            initial["worth_watching"] = existing_worth.score
        form = MovieScoresForm(initial=initial)

    rating_stats = db_movie.ratings.aggregate(
        average=Avg("score"),
        count=Count("id"),
    )
    worth_stats = db_movie.worth_watching_scores.aggregate(
        average=Avg("score"),
        count=Count("id"),
    )

    videos_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos"
    videos_response = requests.get(
        videos_url,
        headers=_tmdb_headers(),
        timeout=10,
    )

    trailer_key = None
    if videos_response.status_code == 200:
        videos_data = videos_response.json()
        for video in videos_data.get("results", []):
            if video.get("site") == "YouTube" and video.get("type") == "Trailer":
                trailer_key = video.get("key")
                break

    return render(
        request,
        "movies/movie_detail.html",
        {
            "movie": movie_data,
            "db_movie": db_movie,
            "trailer_key": trailer_key,
            "movie_id": movie_id,
            "form": form,
            "rating_average": rating_stats["average"],
            "rating_count": rating_stats["count"] or 0,
            "worth_average": worth_stats["average"],
            "worth_count": worth_stats["count"] or 0,
        },
    )


def _rated_movies_queryset(order_by):
    return (
        Movie.objects.annotate(
            avg_rating=Avg("ratings__score"),
            rating_count=Count("ratings", distinct=True),
            avg_worth=Avg("worth_watching_scores__score"),
            worth_count=Count("worth_watching_scores", distinct=True),
        )
        .filter(rating_count__gte=1)
        .order_by(order_by, "title")
    )


@login_required
def top_rated(request):
    return render(
        request,
        "movies/rated_list.html",
        {
            "movies": _rated_movies_queryset("-avg_rating"),
            "page_title": "Top Rated",
            "page_blurb": "Movies with the highest community ratings.",
        },
    )


@login_required
def lowest_rated(request):
    return render(
        request,
        "movies/rated_list.html",
        {
            "movies": _rated_movies_queryset("avg_rating"),
            "page_title": "Lowest Rated",
            "page_blurb": "Movies with the lowest community ratings.",
        },
    )


@login_required
def movie_discussion(request, movie_id):
    db_movie, movie_data = upsert_movie_from_tmdb(movie_id)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.movie = db_movie
            comment.parent = None
            comment.save()
            return redirect(
                reverse("movie_discussion", args=[movie_id])
                + f"#comment-{comment.id}"
            )
    else:
        form = CommentForm()

    comments = list(
        Comment.objects.filter(movie=db_movie)
        .select_related("user", "parent")
        .annotate(annotated_score=Sum("votes__value"))
    )
    comment_tree = build_comment_tree(comments, request.user)

    return render(
        request,
        "movies/discussion.html",
        {
            "movie": movie_data,
            "db_movie": db_movie,
            "movie_id": movie_id,
            "form": form,
            "comment_tree": comment_tree,
            "comment_count": len(comments),
        },
    )


@login_required
@require_POST
def reply_comment(request, movie_id, comment_id):
    db_movie, _movie_data = upsert_movie_from_tmdb(movie_id)
    parent = get_object_or_404(Comment, pk=comment_id, movie=db_movie)

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.movie = db_movie
        comment.parent = parent
        comment.save()
        return redirect(
            reverse("movie_discussion", args=[movie_id])
            + f"#comment-{comment.id}"
        )

    return redirect(
        reverse("movie_discussion", args=[movie_id])
        + f"#comment-{parent.id}"
    )


@login_required
@require_POST
def vote_comment(request, movie_id, comment_id):
    db_movie = get_object_or_404(Movie, api_id=str(movie_id))
    comment = get_object_or_404(Comment, pk=comment_id, movie=db_movie)

    try:
        value = int(request.POST.get("value", "0"))
    except (TypeError, ValueError):
        value = 0

    if value not in (CommentVote.UPVOTE, CommentVote.DOWNVOTE):
        return redirect(
            reverse("movie_discussion", args=[movie_id])
            + f"#comment-{comment.id}"
        )

    existing = CommentVote.objects.filter(
        user=request.user,
        comment=comment,
    ).first()

    # Same vote again clears it (always allowed).
    if existing and existing.value == value:
        existing.delete()
        return redirect(
            reverse("movie_discussion", args=[movie_id])
            + f"#comment-{comment.id}"
        )

    current = comment.raw_score()
    if existing:
        projected = current - existing.value + value
    else:
        projected = current + value

    # Do not let the score go below zero.
    if projected < 0:
        return redirect(
            reverse("movie_discussion", args=[movie_id])
            + f"#comment-{comment.id}"
        )

    if existing:
        existing.value = value
        existing.save(update_fields=["value", "updated_at"])
    else:
        CommentVote.objects.create(
            user=request.user,
            comment=comment,
            value=value,
        )

    return redirect(
        reverse("movie_discussion", args=[movie_id])
        + f"#comment-{comment.id}"
    )
