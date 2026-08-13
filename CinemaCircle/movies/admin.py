from django.contrib import admin

from .models import Comment, CommentVote, Movie, Rating, WorthWatching


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "api_id", "release_date")
    search_fields = ("title", "api_id")


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "score", "updated_at")
    list_filter = ("score",)


@admin.register(WorthWatching)
class WorthWatchingAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "score", "updated_at")
    list_filter = ("score",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "parent", "created_at")
    search_fields = ("body", "user__username", "movie__title")
    list_filter = ("created_at",)


@admin.register(CommentVote)
class CommentVoteAdmin(admin.ModelAdmin):
    list_display = ("user", "comment", "value", "updated_at")
    list_filter = ("value",)
