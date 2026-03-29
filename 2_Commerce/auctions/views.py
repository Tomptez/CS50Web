from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from .models import User, AuctionListing, Bid, Wishlist, Comment
from django.urls import reverse
from .forms import ListingForm, CommentForm
from django.db.models import Max
from decimal import Decimal

def get_current_bid_amount(auctionlisting):
    maxbid = auctionlisting.bids.all().aggregate(Max('amount'))
    if maxbid["amount__max"] is None:
        return 0
    else:
       return maxbid["amount__max"]

def index(request):
    """Return Index view with active listings"""
    listings = AuctionListing.objects.filter(closed=False).annotate(
        highest_bid=Max('bids__amount')
    )

    if request.user:
        wishlist_items = AuctionListing.objects.filter(wishlists__user=request.user.id)
    return render(request, "auctions/index.html", context={"listings": listings, "wishlist": wishlist_items})

@login_required
def make_a_bid(request):
    if request.method == 'POST':
        r = request.POST
        if not r.get("auction"):
            print(r)
            print("field missing")
            raise Exception
        auction = get_object_or_404(AuctionListing, pk=r.get("auction"))
        # Use this to close the auction if done by the creator
        if auction.creator == request.user:
            auction.closed = True
            auction.save()
            return HttpResponseRedirect(reverse("listing_detail", kwargs={'listing_id': r.get("auction")}))
        elif not r.get("bidamount"):
            raise Exception("No Bid Amount")
        try:
            bid_amount = Decimal(r.get("bidamount"))
            if get_current_bid_amount(auction) >= bid_amount or auction.minBid > bid_amount:
                print("Bid is not high enough")
                return HttpResponseRedirect(reverse("listing_detail", kwargs={'listing_id': r.get("auction")}))
            else:
                Bid.objects.create(user_id=request.user.id, auction_id=auction.id, amount=bid_amount)
                return HttpResponseRedirect(reverse("listing_detail", kwargs={'listing_id': r.get("auction")}))
        except Exception:
            print("couldn't handle Bid. Maybe form contained a string or some other tinkering with the bidding form?")
            return HttpResponseRedirect(reverse("listing_detail", kwargs={'listing_id': r.get("auction")}))

def listing_detail(request, listing_id):
    listing = get_object_or_404(AuctionListing, id=listing_id)
    if request.user.is_authenticated:
        isinwishlist = Wishlist.objects.filter(user=request.user.id, auction_id=listing).exists()
        userbid = listing.bids.filter(user_id=request.user.id).aggregate(Max('amount'))["amount__max"]
    else:
        isinwishlist = False
        userbid = None
    maxbid = get_current_bid_amount(listing)
    bid = Bid.objects.filter(auction=listing, amount=maxbid).first()
    comments = Comment.objects.filter(listing=listing)
    comment_form = CommentForm()
    return render(request, "auctions/listing_detail.html", context={"listing": listing, "maxbid": maxbid, "bid": bid, "isinwishlist": isinwishlist, "userbid": userbid, "comments": comments, "comment_form": comment_form})

@login_required
def post_comment(request):
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)  # don’t save yet
            comment.author = request.user
            comment.listing_id = request.POST.get("listing_id")
            comment.save()
            return HttpResponseRedirect(reverse("listing_detail", kwargs={'listing_id': request.POST.get("listing_id")}))
        listing_id = request.POST.get("listing_id")
        if listing_id:
            return HttpResponseRedirect(reverse("listing_detail", kwargs={'listing_id': listing_id}))
    return HttpResponseRedirect(reverse("index"))
def categories(request):
    categories  = AuctionListing.category.field.choices
    all_categories = {}
    for cats in categories:
        all_categories[cats[0]] = cats[1]
    return render(request, "auctions/categories.html", context={"categories": all_categories})


def listings_by_categories(request, cat):
    if request.method == 'GET':
        listings = AuctionListing.objects.filter(closed=False, category=cat)
        if request.user:
            wishlist_items = AuctionListing.objects.filter(wishlists__user=request.user.id)
        return render(request, "auctions/index.html", context={"listings": listings, 'wishlist': wishlist_items})


@login_required
def add_remove_wishlist(request, listing):
    if request.method == 'POST':
        auction = get_object_or_404(AuctionListing, pk=listing)
        if request.POST.get("actiontype") == "remove":
            x = Wishlist.objects.filter(user=request.user, auction=auction)
            x.delete()
            return HttpResponseRedirect(request.META["HTTP_REFERER"])
        else:
            try:
                Wishlist.objects.create(user=request.user, auction=auction)
            except Exception:
                pass # Item is already on wishlist (only occurs in rare cases)
            return HttpResponseRedirect(request.META["HTTP_REFERER"])


@login_required
def wishlist(request):
    user = request.user
    wishlist_items = AuctionListing.objects.filter(wishlists__user=user.id)
    return render(request, "auctions/wishlist.html", context={"listings": wishlist_items})


def login_view(request):
    """Return login.html"""
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(
                request,
                "auctions/login.html",
                {"message": "Invalid username and/or password."},
            )
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


@login_required
def addlisting(request):
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)  # don’t save yet
            post.creator = request.user
            post.save()
            return HttpResponseRedirect(reverse("index"))
    else:
        form = ListingForm()
    context = {"form": form.as_ul()}
    return render(request, "auctions/new_listing.html", context)



def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(
                request, "auctions/register.html", {"message": "Passwords must match."}
            )

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(
                request,
                "auctions/register.html",
                {"message": "Username already taken."},
            )
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
