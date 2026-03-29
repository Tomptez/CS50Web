from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse, HttpResponseForbidden, HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from .models import User, Post
from django.db.models import Count, Exists, OuterRef
from django.core.paginator import Paginator
import json


def _timeline_queryset(user=None):
    if user and user.is_authenticated:
        return Post.objects.annotate(
            like_count=Count("likedby", distinct=True),
            likedbyyou=Exists(
                Post.likedby.through.objects.filter(
                    post_id=OuterRef("pk"), user_id=user.pk
                )
            ),
        ).order_by("-post_created")
    return Post.objects.annotate(
        like_count=Count("likedby", distinct=True)
    ).order_by("-post_created")


def _paginate_posts(queryset, page_number, per_page=10):
    paginator = Paginator(queryset, per_page)
    page = paginator.get_page(page_number)
    return page, paginator


@csrf_protect
def index(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Login required to post.")
        text = request.POST.get("post", "").strip()
        if not text:
            return render(request, "network/index.html", {
                "mainpage": True, "error": "Post text cannot be empty."
            })
        Post.objects.create(author=request.user, text=text)
        return redirect("index")

    page_number = request.GET.get("page", 1)
    queryset = _timeline_queryset(request.user if request.user.is_authenticated else None)
    page, paginator = _paginate_posts(queryset, page_number)
    context = {
        "mainpage": True,
        "timeline": page.object_list,
        "pagenumbers": list(paginator.page_range),
        "page": page,
    }
    return render(request, "network/index.html", context)


@login_required
@csrf_protect
def following(request):
    user = request.user
    queryset = Post.objects.filter(author__in=user.follows.all()).annotate(
        like_count=Count("likedby", distinct=True),
        likedbyyou=Exists(
            Post.likedby.through.objects.filter(
                post_id=OuterRef("pk"), user_id=user.pk
            )
        ),
    ).order_by("-post_created")
    page_number = request.GET.get("page", 1)
    page, paginator = _paginate_posts(queryset, page_number)
    context = {
        "timeline": page.object_list,
        "pagenumbers": list(paginator.page_range),
        "page": page,
    }
    return render(request, "network/index.html", context)


@login_required
@csrf_protect
def follow(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid JSON"}, status=400)
    username = body.get("username")
    if not username:
        return JsonResponse({"error": "username missing"}, status=400)

    target = get_object_or_404(User, username=username)
    if request.user.follows.filter(pk=target.pk).exists():
        request.user.follows.remove(target)
    else:
        request.user.follows.add(target)
    return JsonResponse({"status": "ok"})


@login_required
@csrf_protect
def like(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid JSON"}, status=400)
    post_id = body.get("postId")
    if post_id is None:
        return JsonResponse({"error": "postId missing"}, status=400)

    post = get_object_or_404(Post, pk=post_id)
    if request.user.likedposts.filter(pk=post.pk).exists():
        post.likedby.remove(request.user)
    else:
        post.likedby.add(request.user)
    return JsonResponse({"status": "ok"})


def profile(request, username):
    profile_user = get_object_or_404(
        User.objects.annotate(n_followers=Count("followers"), n_follows=Count("follows")),
        username=username,
    )

    if request.user.is_authenticated:
        is_followed = request.user.follows.filter(pk=profile_user.pk).exists()
        timeline = Post.objects.filter(author=profile_user).annotate(
            like_count=Count("likedby", distinct=True),
            likedbyyou=Exists(
                Post.likedby.through.objects.filter(
                    post_id=OuterRef("pk"), user_id=request.user.pk
                )
            ),
        ).order_by("-post_created")
    else:
        is_followed = False
        timeline = Post.objects.filter(author=profile_user).annotate(
            like_count=Count("likedby", distinct=True)
        ).order_by("-post_created")

    context = {
        "is_followed": is_followed,
        "profile_user": profile_user,
        "timeline": timeline,
    }
    return render(request, "network/profile.html", context)


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        return render(request, "network/login.html", {"message": "Invalid username and/or password."})
    return render(request, "network/login.html")


@login_required
@csrf_protect
def edit(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid JSON"}, status=400)
    postid = data.get("postId")
    if postid is None:
        return JsonResponse({"error": "postId missing"}, status=400)

    post = get_object_or_404(Post, pk=postid)
    if post.author != request.user:
        return JsonResponse({"error": "forbidden"}, status=403)

    post.text = (data.get("text") or "").strip()
    post.save()
    return JsonResponse({"status": "ok"})


def logout_view(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {"message": "Passwords must match."})

        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {"message": "Username already taken."})
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    return render(request, "network/register.html")


@login_required
def create_new_post(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    text = request.POST.get("post_text", "").strip()
    if not text:
        return JsonResponse({"error": "Post text cannot be empty."}, status=400)
    Post.objects.create(author=request.user, text=text)
    return redirect("index")