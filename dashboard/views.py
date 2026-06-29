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
import requests
import wikipedia
from django.contrib.auth.decorators import login_required


API_KEY = settings.YOUTUBE_API_KEY


# Create your views here.
def home(request):
    return render(request, 'dashboard/home.html')

@login_required
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

@login_required
def delete_note(request,pk=None):
    Notes.objects.get(id=pk).delete()
    return redirect("notes")


class NotesDetailView(generic.DetailView):
    model = Notes

@login_required
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

@login_required
def update_homework(request,pk=None):
    homework = Homework.objects.get(id=pk)
    if homework.is_finished == True:
        homework.is_finished = False
    else:
        homework.is_finished = True
    homework.save()
    return redirect('homework')

@login_required
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

@login_required
def todo(request):
    if request.method == "POST":
        form = TodoForm(request.POST)
        if form.is_valid():
            try:
                finished = request.POST["is_finished"]
                if finished == 'on':
                    finished = True
                else:
                    finished = False
            except:
                finished = False
            todos = Todo(
                user = request.user,
                title = request.POST['title'],
                is_finished = finished
            )
            todos.save()
            messages.success(request,f"Todo Added from {request.user.username}!!")
    else:
        form = TodoForm()
    todo = Todo.objects.filter(user=request.user)
    if len(todo) == 0:
        todos_done = True
    else:
        todos_done = False
    context = {
        'form':form,
        'todos':todo,
        'todos_done':todos_done
    }
    return render(request, "dashboard/todo.html",context)

@login_required
def update_todo(request,pk=None):
    todo = Todo.objects.get(id=pk)
    if todo.is_finished == True:
        todo.is_finished = False
    else:
        todo.is_finished = True
    todo.save()
    return redirect('todo')

@login_required
def delete_todo(request,pk=None):
    Todo.objects.get(id=pk).delete()
    return redirect('todo')

def books(request):
    form = DashboardForm()
    context = {
        'form':form,
    }
    return render(request, "dashboard/books.html", context)

def books(request):
    form = DashboardForm()
    result_list = []

    if request.method == "POST":
        form = DashboardForm(request.POST)

        if form.is_valid():
            text = form.cleaned_data['text']

            url = f"https://www.googleapis.com/books/v1/volumes?q={text}&key={settings.GOOGLE_BOOKS_API_KEY}"
            r = requests.get(url)
            answer = r.json()

            # print(answer)   # Debugging

            items = answer.get("items", [])

            for item in items[:10]:
                volume = item.get("volumeInfo", {})

                result_dict = {
                    'title': volume.get('title'),
                    'subtitle': volume.get('subtitle'),
                    'description': volume.get('description'),
                    'count': volume.get('pageCount'),
                    'categories': volume.get('categories'),
                    'rating': volume.get('averageRating'),
                    'thumbnail': volume.get('imageLinks', {}).get('thumbnail'),
                    'preview': volume.get('previewLink'),
                }

                result_list.append(result_dict)

    context = {
        'form': form,
        'results': result_list,
    }

    return render(request, "dashboard/books.html", context)

def dictionary(request):
    if request.method == "POST":
        form = DashboardForm(request.POST)

        if form.is_valid():
            text = form.cleaned_data['text']

            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{text}"
            r = requests.get(url)
            answer = r.json()

            try:
                phonetics = answer[0]['phonetics'][0].get('text', '')
                audio = answer[0]['phonetics'][0].get('audio', '')
                definition = answer[0]['meanings'][0]['definitions'][0].get('definition', '')
                example = answer[0]['meanings'][0]['definitions'][0].get('example', '')
                synonyms = answer[0]['meanings'][0]['definitions'][0].get('synonyms', [])

                context = {
                    'form': form,
                    'input': text,
                    'phonetics': phonetics,
                    'audio': audio,
                    'definition': definition,
                    'example': example,
                    'synonyms': synonyms,
                }

            except (KeyError, IndexError):
                context = {
                    'form': form,
                    'input': "",
                }

            return render(request, "dashboard/dictionary.html", context)

    else:
        form = DashboardForm()

    context = {
        'form': form,
    }

    return render(request, "dashboard/dictionary.html", context)

def wiki(request):
    if request.method == "POST":
        text = request.POST['text']
        form = DashboardForm(request.POST)
        search = wikipedia.page(text)
        context = {
            'form':form,
            'title':search.title,
            'link':search.url,
            'details':search.summary
        }
        return render(request, "dashboard/wiki.html",context)
    else:
        form = DashboardForm()
        context = {
            'form':form
        }
    return render(request, "dashboard/wiki.html",context)


def conversion(request):
    form = ConversionForm(request.POST or None)
    m_form = None
    answer = ""
    show_input = False

    if request.method == "POST" and form.is_valid():

        measurement = form.cleaned_data["measurement"]
        show_input = True

        if measurement == "length":
            m_form = ConversionLengthForm(request.POST or None)

            if m_form.is_valid():
                value = float(m_form.cleaned_data["input"])
                first = m_form.cleaned_data["measure1"]
                second = m_form.cleaned_data["measure2"]

                if first == "yard" and second == "foot":
                    answer = f"{value:g} Yard = {(value*3):g} Foot"

                elif first == "foot" and second == "yard":
                    answer = f"{value:g} Foot = {(value/3):g} Yard"

        elif measurement == "mass":
            m_form = ConversionMassForm(request.POST or None)

            if m_form.is_valid():
                value = float(m_form.cleaned_data["input"])
                first = m_form.cleaned_data["measure1"]
                second = m_form.cleaned_data["measure2"]

                if first == "pound" and second == "kilogram":
                    answer = f"{value:g} Pound = {(value*0.453592):g} Kilogram"

                elif first == "kilogram" and second == "pound":
                    answer = f"{value:g} Kilogram = {(value*2.20462):g} Pound"

    context = {
        "form": form,
        "m_form": m_form,
        "input": show_input,
        "answer": answer,
    }

    return render(request, "dashboard/conversion.html", context)

def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request,f"Account Created for {username}!!")
            return redirect("login")
    else:
        form = UserRegistrationForm()
    context = {
        'form':form
    }
    return render(request, "dashboard/register.html",context)

@login_required
def profile(request):
    homeworks = Homework.objects.filter(is_finished=False,user=request.user)
    todos = Todo.objects.filter(is_finished=False,user=request.user)
    if len(homeworks) == 0:
        homework_done = True
    else:
        homework_done = False
    if len(todos) == 0:
        todos_done = True
    else:
        todos_done = False
    context = {
        'homeworks':homeworks,
        'todos':todos,
        'homework_done':homework_done,
        'todos_done':todos_done
    }
    return render(request, "dashboard/profile.html",context)