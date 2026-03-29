import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse

from .models import User, Email, EmailRecipient


def index(request):
    # Authenticated users view their inbox
    if request.user.is_authenticated:
        return render(request, "mail/inbox.html")

    # Everyone else is prompted to sign in
    else:
        return HttpResponseRedirect(reverse("login"))


@login_required
def compose(request):
    # Composing a new email must be via POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    emails = [email.strip() for email in data.get("recipients", "").split(",") if email.strip()]
    if not emails:
        return JsonResponse({"error": "At least one recipient required."}, status=400)

    recipients = []
    for email_addr in emails:
        try:
            user = User.objects.get(email=email_addr)
            recipients.append(user)
        except User.DoesNotExist:
            return JsonResponse({"error": f"User with email {email_addr} does not exist."}, status=400)

    subject = data.get("subject", "")
    body = data.get("body", "")

    email = Email.objects.create(
        sender=request.user,
        subject=subject,
        body=body
    )

    for recipient in recipients:
        EmailRecipient.objects.create(email=email, recipient=recipient, read=False, archived=False)

    return JsonResponse({"message": "Email sent successfully."}, status=201)

@login_required
def mailbox(request, mailbox):
    if mailbox in ("inbox", "archive"):
        entries = EmailRecipient.objects.filter(
            recipient=request.user,
            archived=(mailbox == "archive")
        ).select_related("email__sender", "recipient")
        emails = [e.email.serialize(status=e) for e in entries]
    elif mailbox == "sent":
        sent = Email.objects.filter(sender=request.user).prefetch_related("recipients")
        emails = [e.serialize() for e in sent]
    else:
        return JsonResponse({"error": "Invalid mailbox."}, status=400)
    return JsonResponse(emails, safe=False)


@login_required
def email(request, email_id):
    recipient_status = EmailRecipient.objects.filter(email_id=email_id, recipient=request.user).select_related("email").first()
    email = None

    if recipient_status:
        email = recipient_status.email
    else:
        # allow sender to view their sent email
        try:
            email = Email.objects.get(pk=email_id, sender=request.user)
        except Email.DoesNotExist:
            return JsonResponse({"error": "Email not found."}, status=404)

    if request.method == "GET":
        return JsonResponse(email.serialize(status=recipient_status))

    elif request.method == "PUT":
        if recipient_status is None:
            return JsonResponse({"error": "Only recipients can modify read/archive status."}, status=403)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)
        if data.get("read") is not None:
            recipient_status.read = data["read"]
        if data.get("archived") is not None:
            recipient_status.archived = data["archived"]
        recipient_status.save()
        return HttpResponse(status=204)

    else:
        return JsonResponse({"error": "GET or PUT request required."}, status=400)


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(request, username=email, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "mail/login.html", {
                "message": "Invalid email and/or password."
            })
    else:
        return render(request, "mail/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "mail/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(email, email, password)
            user.save()
        except IntegrityError as e:
            print(e)
            return render(request, "mail/register.html", {
                "message": "Email address already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "mail/register.html")
