from django.shortcuts import render, redirect
from django import forms
from random import sample
from markdown2 import Markdown
markdowner = Markdown()

from . import util

class NewPageForm(forms.Form):
  title = forms.CharField(label="Title")
  content = forms.CharField(widget=forms.Textarea(attrs={"rows":"5"}), label="Page content")  
  
class EditPageForm(forms.Form):
  content = forms.CharField(widget=forms.Textarea(attrs={"rows":"5"}))  
  

def index(request):
    params = request.GET
    query = params.get("q")
    entries = {e.lower():e for e in util.list_entries()}
    if query is None:
        return render(request, "encyclopedia/index.html", {
                "entries": util.list_entries()
            })
    elif query.lower() in entries.keys():
        return redirect("entry", entries[query.lower()])
    else:
        return searchresults(request, query)

def searchresults(request, query):
    list_entries  = []
    for entry in util.list_entries():
        if query.lower() in entry.lower():
            list_entries.append(entry)
    return render(request, "encyclopedia/searchresults.html", {
        "entries": list_entries
}) 


def entry(request, title):
    entry = util.get_entry(title)
    if entry is None:
        return render(request, "encyclopedia/404.html", {"title": title})
    else:
        entry = markdowner.convert(entry)
        return render(request, "encyclopedia/entry.html", {
            "entry": entry,
            "title": title
        })

def randompage(request):
    return redirect(f"/wiki/{sample(util.list_entries(), 1)[0]}")

def newpage(request):
    if request.method == "POST":
        form = NewPageForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data["title"]
            content = form.cleaned_data["content"]
            if title in util.list_entries():
               return render(request, "encyclopedia/newpage.html", {
                    "form": form,
                    "error": "<span class='errormessage'><i>Title already exists</i></span>"
                })
            else:
                util.save_entry(title, f"{content}")
                return redirect("entry", title)
    else:
        return render(request, "encyclopedia/newpage.html", {
            "form": NewPageForm(),
            "error": None
        })

def editpage(request, title=None):
    if request.method == "POST":
        form = EditPageForm(request.POST)
        if form.is_valid():
            content = form.cleaned_data["content"]
            util.save_entry(title, f"{content}")
        return redirect(f"/wiki/{title}")
    else:
        entry = util.get_entry(title)
        return render(request, "encyclopedia/editpage.html", {
            "form": EditPageForm(initial={"content": entry}),
            "title": title
        })