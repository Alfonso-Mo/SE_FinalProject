from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum


class Movie(models.Model):
    api_id = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    overview = models.TextField(blank=True)
    poster_url = models.URLField(blank=True)
    release_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["title"] #testing

    def __str__(self):
        return self.title


class Rating(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "movie"],
                name="unique_rating_per_user_movie",
            ),
        ]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user} rated {self.movie} {self.score}/10"


class WorthWatching(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="worth_watching_scores",
    )
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="worth_watching_scores",
    )
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "movie"],
                name="unique_worth_watching_per_user_movie",
            ),
        ]
        ordering = ["-updated_at"]
        verbose_name_plural = "worth watching scores"

    def __str__(self):
        return f"{self.user} worth-watching {self.movie} {self.score}/10"


class Comment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.user} on {self.movie}"

    def raw_score(self):
        if hasattr(self, "annotated_score") and self.annotated_score is not None:
            return self.annotated_score
        total = self.votes.aggregate(total=Sum("value"))["total"]
        return total or 0

    @property
    def score(self):
        return max(0, self.raw_score())


class CommentVote(models.Model):
    UPVOTE = 1
    DOWNVOTE = -1
    VALUE_CHOICES = (
        (UPVOTE, "Upvote"),
        (DOWNVOTE, "Downvote"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comment_votes",
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    value = models.SmallIntegerField(choices=VALUE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "comment"],
                name="unique_vote_per_user_comment",
            ),
        ]

    def __str__(self):
        return f"{self.user} voted {self.value} on comment {self.comment_id}"
