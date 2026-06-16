from django.shortcuts import render, redirect
from . forms import *
from django.views import generic
from django.contrib import messages
from youtubesearchpython import VideosSearch
from . import patches

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

def youtube(request):
    if request.method == "POST":
        form = DashboardForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data.get('text')
            video = VideosSearch(text, limit=10)
            result_list = []
            
            results = video.result() or {}
            for item in results.get('result', []):
                # Safely extract thumbnails URL
                thumbnails = item.get('thumbnails') or []
                thumbnail_url = thumbnails[0].get('url', '') if thumbnails else ''
                
                # Safely extract channel name
                channel_data = item.get('channel') or {}
                channel_name = channel_data.get('name', '')

                # Safely extract views count
                view_data = item.get('viewCount') or {}
                view_count = view_data.get('short', '')

                # Safely compile description snippets
                description_snippet = item.get('descriptionSnippet') or []
                desc = "".join(j.get('text', '') for j in description_snippet if isinstance(j, dict))

                result_list.append({
                    'input': text,
                    'title': item.get('title'),
                    'duration': item.get('duration'),
                    'thumbnail': thumbnail_url,
                    'channel': channel_name,
                    'link': item.get('link'),
                    'views': view_count,
                    'published': item.get('publishedTime'),
                    'description': desc,
                })
            
            context = {
                'form': form,
                'results': result_list
            }
            return render(request, "dashboard/youtube.html", context)
    else:
        form = DashboardForm()
    context = {'form': form}
    return render(request, "dashboard/youtube.html", context)