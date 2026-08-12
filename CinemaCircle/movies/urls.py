from django.urls import path #added my code form codespaces
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="login"), name="root"),
    path("home/", views.home, name="home"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    
    # ADDED THIS LINE FOR THE WATCH TRAILER FEATURE:
    path("movie/<int:movie_id>/", views.movie_detail, name="movie_detail"),
]