from django.shortcuts import render, redirect
from . forms import *
from django.views import generic
from django.contrib import messages
# from youtubesearchpython import VideosSearch
from django.conf import settings
from googleapiclient.discovery import build
from isodate import parse_duration
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta


API_KEY = settings.YOUTUBE_API_KEY


# Create your views here.
def home(request):
    return render(request, 'dashboard/home.html')
def notes(request):
    if request.method == "POST":
        form = NotesForm(request.POST)
        if form.is_valid():
            notes = Notes(user=request.user,title=request.POST['title'], description=request.POST['description'])
            notes.save()
        messages.success(request,f"Notes Added from {request.user.username} Successfull")
    else:
        form = NotesForm()
    notes = Notes.objects.filter(user=request.user)
    context = {'notes':notes, 'form':form}
    return render(request, 'dashboard/notes.html', context)

def delete_note(request,pk=None):
    Notes.objects.get(id=pk).delete()
    return redirect("notes")

class NotesDetailView(generic.DetailView):
    model = Notes

def homework(request):
    if request.method == "POST":
        form = HomeworkForm(request.POST)
        if form.is_valid():
            try:
                finished = request.POST['is_finished']
                if finished == 'on':
                    finished = True
                else:
                    finished = False
            except:
                finished = False
            homeworks = Homework(
                user = request.user,
                subject = request.POST['subject'],
                title = request.POST['title'],
                description = request.POST['description'],
                due = request.POST['due'],
                is_finished = finished
            )
            homeworks.save()
            messages.success(request,f"Homework added from {request.user.username}!!")
    else:
        form = HomeworkForm()
                
    homework = Homework.objects.filter(user=request.user)
    if len(homework) == 0:
        homework_done = True
    else:
        homework_done = False
    context = {
        'homeworks':homework, 'homeworks_done':homework_done,
        'form':form,
    }
    return render(request, 'dashboard/homework.html', context)

def update_homework(request,pk=None):
    homework = Homework.objects.get(id=pk)
    if homework.is_finished == True:
        homework.is_finished = False
    else:
        homework.is_finished = True
    homework.save()
    return redirect('homework')

def delete_homework(request,pk=None):
    Homework.objects.get(id=pk).delete()
    return redirect('homework')


def time_ago(published_at):
    published_date = datetime.strptime(
        published_at,
        "%Y-%m-%dT%H:%M:%SZ"
    ).replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    diff = relativedelta(now, published_date)

    if diff.years > 0:
        return f"{diff.years} year{'s' if diff.years > 1 else ''} ago"
    elif diff.months > 0:
        return f"{diff.months} month{'s' if diff.months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.hours > 0:
        return f"{diff.hours} hour{'s' if diff.hours > 1 else ''} ago"
    else:
        return "Just now"


def youtube(request):
    form = DashboardForm()
    result_list = []

    if request.method == "POST":
        form = DashboardForm(request.POST)

        if form.is_valid():
            text = form.cleaned_data['text']

            youtube = build(
                "youtube",
                "v3",
                developerKey=settings.YOUTUBE_API_KEY
            )

            search_response = youtube.search().list(
                q=text,
                part="snippet",
                maxResults=10,
                type="video"
            ).execute()

            video_ids = [
                item["id"]["videoId"]
                for item in search_response["items"]
            ]

            video_response = youtube.videos().list(
                part="contentDetails,statistics",
                id=",".join(video_ids)
            ).execute()

            video_details = {}

            for item in video_response["items"]:
                views_count = int(
                    item["statistics"].get("viewCount", 0)
                )

                if views_count >= 1_000_000:
                    views = f"{views_count / 1_000_000:.1f}M views"
                elif views_count >= 1_000:
                    views = f"{views_count / 1_000:.1f}K views"
                else:
                    views = f"{views_count} views"

                duration = str(
                    parse_duration(
                        item["contentDetails"]["duration"]
                    )
                )

                video_details[item["id"]] = {
                    "duration": duration,
                    "views": views,
                }

            for item in search_response["items"]:
                video_id = item["id"]["videoId"]

                result_dict = {
                    "input": text,
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                    "channel": item["snippet"]["channelTitle"],
                    "link": f"https://www.youtube.com/watch?v={video_id}",
                    "published": time_ago(
                        item["snippet"]["publishedAt"]
                    ),
                    "duration": video_details.get(
                        video_id, {}
                    ).get("duration", "N/A"),
                    "views": video_details.get(
                        video_id, {}
                    ).get("views", "N/A"),
                }

                result_list.append(result_dict)

    context = {
        "form": form,
        "results": result_list,
    }

    return render(
        request,
        "dashboard/youtube.html",
        context
    )

def todo(request):
    return render(request, "dashboard/todo.html")