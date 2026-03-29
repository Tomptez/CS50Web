from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    id = models.AutoField(primary_key=True)

class AuctionListing(models.Model):
    CATEGORIES = (
        ("fash", "Fashion"),
        ("toys", "Toys"),
        ("elec", "Electronics"),
        ("home", "Home"),
        ("outd", "Outdoor")
    )
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    imageUrl = models.CharField(max_length=60, default="defaultimg.png")
    category = models.CharField(max_length=4, choices=CATEGORIES)
    description = models.CharField(max_length=1000, null=True)
    minBid = models.IntegerField(default=0)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    closed = models.BooleanField(default=False)

class Bid(models.Model):
    id = models.AutoField(primary_key=True)
    auction = models.ForeignKey(AuctionListing, related_name="bids", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2, max_digits=9)

class Wishlist(models.Model):
    user = models.ForeignKey(User, related_name="wishlist", on_delete=models.CASCADE)
    auction = models.ForeignKey(AuctionListing, related_name="wishlists", on_delete=models.CASCADE)

    class Meta:
        unique_together = (("user", "auction"))

class Comment(models.Model):
    listing = models.ForeignKey(AuctionListing, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=800)
    created_at = models.DateTimeField(auto_now_add=True)