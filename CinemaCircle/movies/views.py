from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View


def home(request):
    return render(request, "movies/homepage.html")


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
    redirect_authenticated_user = True


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("home")
