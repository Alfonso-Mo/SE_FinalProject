from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="login"), name="root"),
    path("home/", views.home, name="home"),
    path("discussions/", views.discussions_list, name="discussions_list"),
    path("top-rated/", views.top_rated, name="top_rated"),
    path("lowest-rated/", views.lowest_rated, name="lowest_rated"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("movie/<int:movie_id>/", views.movie_detail, name="movie_detail"),
    path(
        "movie/<int:movie_id>/discussion/",
        views.movie_discussion,
        name="movie_discussion",
    ),
    path(
        "movie/<int:movie_id>/comment/<int:comment_id>/reply/",
        views.reply_comment,
        name="reply_comment",
    ),
    path(
        "movie/<int:movie_id>/comment/<int:comment_id>/vote/",
        views.vote_comment,
        name="vote_comment",
    ),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
]