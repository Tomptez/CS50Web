from django.contrib.auth.models import AbstractUser
from django.db import models
from django import utils

class User(AbstractUser):
    follows = models.ManyToManyField("User", related_name="followers")
    account_created = models.DateTimeField(default=utils.timezone.now)

class Post(models.Model):
    author = models.ForeignKey("User", related_name="posts", on_delete=models.SET_NULL, null=True)
    text = models.CharField(max_length=360, null=False)
    likedby = models.ManyToManyField("User", related_name="likedposts")

    post_created = models.DateTimeField(default=utils.timezone.now)

    class Meta:
        ordering = ["-post_created"]
