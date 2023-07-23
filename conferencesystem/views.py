from .models import Conference, Paper, Author, Reviewer, Review
from .forms import RegistrationForm, PaperSubmissionForm, ReviewForm

from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse, HttpResponseForbidden, FileResponse

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

def index(request):
    return render(request, 'index.html')

def conferences(request):
    conferences = Conference.objects.all()
    return render(request, 'view_conferences.html', {'conferences': conferences})

def signup(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('conferencesystem:profile')
    else:
        form = RegistrationForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('conferencesystem:profile')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def profile(request):
    user = request.user
    return render(request, 'profile.html', {'user': user})

@login_required
def logout_view(request):
    logout(request)
    return render(request, 'logout.html')  # Redirect to the desired page after logout

@login_required
def submit_paper(request, conference_id):
    conference = get_object_or_404(Conference, id=conference_id)
    if request.method == 'POST':
        form = PaperSubmissionForm(conference, request.POST, request.FILES)
        if form.is_valid():
            paper = form.save(commit=False)
            paper.conference = conference
            paper.save()    # can't directly save form as that would also save m2m

            # Add the paper authors to the conference authors
            authors = []

            selected_users = list(form.cleaned_data['authors'])
            selected_users.append(request.user)
            for user in selected_users:
                author, created = Author.objects.get_or_create(user=user)
                author.conferences.add(conference)  # if the author is already part of the conference, nothing will happen
                authors.append(author)

                # author_exists = Author.objects.filter(user=user, conference=conference).exists()
                # if not author_exists:
                    # author = Author.objects.create(user=user)
                    # author.conferences.add(conference)
                    # authors.append(author)
                # else:
                    # authors.append(Author.objects.filter(user=user, conference=conference).get())

            paper.authors.set(authors)
            paper.save()

            return redirect('conferencesystem:paper_detail', paper_id=paper.id)  # Redirect to paper detail page
    else:
        form = PaperSubmissionForm(conference)

    return render(request, 'submit_paper.html', {'form': form})

@login_required
def paper_detail(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)

    if not paper.is_author(request.user) and not paper.conference.is_chair(request.user):
        return HttpResponseForbidden('You are not authorized.')

    user_is_program_chair = paper.conference.chair_set.filter(user=request.user).exists()
    user_is_reviewer = paper.reviewer_set.filter(user=request.user).exists()

    review_exists = user_is_reviewer and paper.review_set.filter(reviewer__user=request.user).exists()

    context = {
        'paper': paper,
        'submissions_open': paper.conference.submissions_open(),
        'user_is_program_chair': user_is_program_chair,
        'user_is_reviewer': user_is_reviewer,
        'review_exists': review_exists,
    }

    return render(request, 'paper_detail.html', context)

@login_required
def download_paper(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)

    # Perform permission check
    if not request.user.is_superuser and not request.user.is_staff:
        if not paper.is_author(request.user) and not paper.conference.is_chair(request.user):
            return HttpResponseForbidden("You don't have permission to download this file.")

    # Generate the file path
    file_path = paper.file.path

    # Send the file as a response
    response = FileResponse(open(file_path, 'rb'))
    response['Content-Disposition'] = 'attachment; filename="{0}"'.format(paper.file.name)

    return response

@login_required
def view_user_papers(request):
    user = request.user
    papers = Paper.objects.filter(authors__user=user)

    return render(request, 'view_user_papers.html', {'papers': papers})

def conference_details(request, conference_id):
    conference = Conference.objects.get(id=conference_id)
    submissions_open = conference.submissions_open()

    user_is_program_chair = False

    if request.user.is_authenticated:
        user_is_program_chair = conference.chair_set.filter(user=request.user).exists()

    context = {
        'conference': conference,
        'submissions_open': submissions_open,
        'user_is_program_chair': user_is_program_chair,
    }

    return render(request, 'conference_details.html', context)

@login_required
def view_conference_papers(request, conference_id):
    conference = get_object_or_404(Conference, id=conference_id)

    if not conference.is_chair(request.user):
        return HttpResponseForbidden("You are not authorized.")

    tracks = conference.track_set.all()

    papers_by_track = {}
    for track in tracks:
        papers_by_track[track] = conference.paper_set.filter(track=track)

    context = {
        'conference': conference,
        'papers_by_track': papers_by_track,
    }

    return render(request, 'view_conf_papers.html', context)

@login_required
def add_reviewers(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)

    if not paper.conference.is_chair(request.user):
        return HttpResponseForbidden("You are not authorized to add reviewers to this conference.")

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        reviewer, created = Reviewer.objects.get_or_create(user_id=user_id)

        if paper not in reviewer.papers.all():
            reviewer.papers.add(paper)
        
        if paper.status == 'submitted':
            paper.status = 'under_review'
            paper.save()

    reviewers = paper.reviewer_set.all()
    users = User.objects.all()

    context = {
        'paper': paper,
        'reviewers': reviewers,
        'users': users,
    }

    return render(request, 'add_reviewers.html', context)

@login_required
def remove_reviewer(request, paper_id, reviewer_id):
    paper = get_object_or_404(Paper, id=paper_id)
    reviewer = get_object_or_404(Reviewer, id=reviewer_id)

    if not paper.conference.is_chair(request.user):
        return HttpResponseForbidden("You are not authorized to remove reviewers from this conference.")

    if request.method == 'POST':
        try:
            review = Review.objects.get(paper=paper, reviewer=reviewer)
        except Review.DoesNotExist:
            review = None

        if review:
            review.delete()

        reviewer.papers.remove(paper)

    return redirect('conferencesystem:add_reviewers', paper_id=paper.id)

@login_required
def review_paper(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)

    if not paper.is_reviewer(request.user):
        return HttpResponseForbidden("You are not authorized to review this paper.")

    reviewer = get_object_or_404(Reviewer, user=request.user)
    review = Review.objects.filter(reviewer__user=request.user, paper=paper).first()

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = reviewer
            review.paper = paper
            review.save()
            return redirect('conferencesystem:paper_detail', paper_id=paper_id)
    else:
        form = ReviewForm(instance=review)
    return render(request, 'review_paper.html', {'form': form, 'paper': paper})
