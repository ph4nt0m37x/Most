from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.contrib.messages.api import success
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.urls import reverse

from mostApp.forms import *
from mostApp.models import *


# Create your views here.

def my_profile_id(request):
    return request.user.id

def signup(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        password_confirm = request.POST['password_confirm']

        if password == password_confirm:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email is Taken')
                return redirect('signup')
            else:
                user = User.objects.create_user(username=email, email=email, password=password)
                user.save()

                auth.login(request, auth.authenticate(username=email, password=password))

                user_model = User.objects.filter(email=email).first()
                new_profile = Profile.objects.create(user=user_model, first_name=first_name, last_name=last_name)
                new_profile.save()
                return redirect('tutorial')
        else:
            messages.info(request, 'Passwords Not Matching')
            return redirect('signup')
    else:
        return render(request, 'signup.html')

def signin(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = auth.authenticate(username=email, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Invalid Credentials')
            return redirect('signin')
    else:
        return render(request, 'signin.html')

@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')

@login_required(login_url='signin')
def tutorial(request):
    return render(request, 'tutorial.html', context={'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def help_page(request):
    return render(request, 'help.html', context={'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def about(request):
    return render(request, 'about.html', context={'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def index(request):
    posts = Post.objects.all().order_by('-created')
    my_collaborations = Collaboration.objects.filter(user=request.user)
    collaborations = (Collaboration.objects.filter(collaborator__in=my_collaborations.values_list('collaborator'))).values_list('collaborator')
    mutual_collaborations = Profile.objects.filter(id__in=collaborations)
    profiles = Profile.objects.exclude(user__in=mutual_collaborations.values_list('user')).exclude(user=request.user)[:3]
    mutual = False
    if mutual_collaborations.count() > 0:
        mutual = True
    my_profile = Profile.objects.get(user=request.user)
    return render(request, 'index.html',
                  context={'posts': posts,
                           'my_profile': my_profile,
                           'mutuals': mutual_collaborations[:3],
                           'profiles': profiles,
                           'mutual': mutual,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def search(request):
    query = request.GET.get('query')
    profiles_search = Profile.objects.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query))
    my_collaborations = Collaboration.objects.filter(user=request.user)
    collaborations = (
        Collaboration.objects.filter(collaborator__in=my_collaborations.values_list('collaborator'))).values_list(
        'collaborator')
    mutual_collaborations = Profile.objects.filter(id__in=collaborations)
    profiles = Profile.objects.exclude(user__in=mutual_collaborations.values_list('user')).exclude(user=request.user)[
               :3]
    mutual = False
    if mutual_collaborations.count() > 0:
        mutual = True
    return render(request, 'search.html',
                  context={'profiles': profiles,
                           'profiles_search': profiles_search,
                           'query': query,
                           'mutuals': mutual_collaborations[:3],
                           'mutual': mutual,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def browse(request):
    posts = ApplicationPost.objects.all().order_by('-created')
    tags = Tag.objects.all()
    bookmarked = False
    return render(request, 'browse.html',
                  context={'posts': posts,
                           'tags': tags,
                           'bookmarked': bookmarked,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def browse_search(request):
    tags = Tag.objects.all()
    query = request.GET.get('query')
    posts = ApplicationPost.objects.filter(Q(title__icontains=query) |
                                           Q(short_description__icontains=query) |
                                           Q(profile__first_name__icontains=query) |
                                           Q(profile__last_name__icontains=query))
    return render(request, 'browse.html',
                  context={'posts': posts,
                           'tags': tags,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def browse_filter(request):
    date_filter = request.GET.get('date_filter')
    filter_option = request.GET.getlist('filter')
    posts = ApplicationPost.objects.all()
    if date_filter.__contains__('-'):
        date = date_filter.split('-')
        posts = ApplicationPost.objects.filter(created__year__lte=date[0],
                                               created__month__lte=date[1],
                                               created__day__lte=date[2])
    if len(filter_option) == 0:
        filter = 'all'
    else:
        if filter_option[0] == 'all':
            filter = 'all'
        else:
            posts = posts.filter(tag__name__in=filter_option)
            filter = filter_option[0]
    tags = Tag.objects.all()
    return render(request, 'browse.html',
                  context={'posts': posts,
                           'tags': tags,
                           'filter': filter,
                           'date_filter': date_filter,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def create_post(request):
    content = request.POST.get('content')
    image = request.POST.get('image')
    location = request.POST.get('location')
    post = Post.objects.create(content=content, image=image,
                               location=location, profile=Profile.objects.get(user=request.user))
    post.save()
    return redirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='signin')
def create_app_post(request):
    if request.method == 'POST':
        form = ApplicationPostModelForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.profile = Profile.objects.filter(user=request.user).first()
            post.save()
        return redirect('index')

    form = ApplicationPostModelForm()
    return render(request, 'create.html',
                  context={'form': form,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def post(request, post_id):
    exists  = False
    deadline = False  # if the deadline has passed
    post = ApplicationPost.objects.filter(id=post_id).first()
    post_deadline = post.deadline
    if post_deadline is not None:
        if post_deadline.date().__lt__(datetime.today().date()):
            deadline = True
    if ApplicationForm.objects.filter(user=request.user,  app_post_id=post_id).exists():
        exists = True
    return render(request, 'details.html',
                  context={'post': post,
                           'exists': exists,
                           'deadline': deadline,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def apply(request, post_id):
    apply_post = True # if the user tries to apply to their own post
    profile = Profile.objects.filter(user=request.user).first()
    if ApplicationPost.objects.filter(id=post_id).first().profile == profile:
        apply_post = False
    if request.method == 'POST':
        form = ApplicationFormModelForm(request.POST, request.FILES)
        if form.is_valid():
            form = form.save(commit=False)
            form.app_post = ApplicationPost.objects.filter(id=post_id).first()
            form.user = request.user
            form.save()
            return render(request, 'apply.html',
                  context={'form': ApplicationFormModelForm(),
                           'post_id': post_id,
                           'apply': apply_post,
                           'my_profile_id': my_profile_id(request),
                           'successful': True})
    form = ApplicationFormModelForm()
    return render(request, 'apply.html',
                  context={'form': form,
                           'post_id': post_id,
                           'apply': apply_post,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def profile(request, user_id):
    successful = False
    edit = False
    user = User.objects.filter(id=user_id).first()
    if request.user == user:  # currently signed-in user
        profile = Profile.objects.filter(user=request.user).first()
        edit = True
    else:
        profile = Profile.objects.filter(user=user).first()
    posts = Post.objects.filter(profile=profile).order_by('-created')
    certifications = Certification.objects.filter(profile=profile).order_by('-date')
    my_collaborations = Collaboration.objects.filter(user=request.user)
    collaborations = (
        Collaboration.objects.filter(collaborator__in=my_collaborations.values_list('collaborator'))).values_list(
        'collaborator')
    mutual_collaborations = Profile.objects.filter(id__in=collaborations)
    profiles = Profile.objects.exclude(user__in=mutual_collaborations.values_list('user')).exclude(user=request.user)[:3]
    mutual = False
    if mutual_collaborations.count() > 0:
        mutual = True
    return render(request, 'profile.html',
                  context={'profile': profile,
                           'profiles': profiles,
                           'posts': posts,
                           'certifications': certifications,
                           'edit': edit,
                           'mutuals': mutual_collaborations[:3],
                           'mutual': mutual,
                           'successful': successful,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def edit_profile(request):
    if request.method == 'POST':
        user = UserEditModelForm(request.POST, request.FILES, instance=request.user)
        profile = ProfileEditModelForm(request.POST, request.FILES,
                                       instance=Profile.objects.filter(user_id=my_profile_id(request)).first())
        if user.is_valid() or profile.is_valid():
            print(request.user.id)
            user.save()
            profile.save()
        return redirect('profile', request.user.pk)
    user = UserEditModelForm(instance=request.user)
    profile = ProfileEditModelForm(instance=Profile.objects.filter(user_id=my_profile_id(request)).first())
    return render(request, 'edit.html',
                  context={'user': user,
                           'profile': profile,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def bookmark_post(request, post_id):
    profile = Profile.objects.filter(user=request.user).first()
    post = Post.objects.filter(id=post_id).first()
    if BookmarkPost.objects.filter(profile=profile, post=post).exists():
        BookmarkPost.objects.filter(profile=profile, post=post).delete()
    else:
        BookmarkPost.objects.create(profile=profile, post=post).save()
    return redirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='signin')
def bookmark_app_post(request, post_id):
    profile = Profile.objects.filter(user=request.user).first()
    post = ApplicationPost.objects.filter(id=post_id).first()
    if BookmarkAppPost.objects.filter(profile=profile, app_post=post).exists():
        BookmarkAppPost.objects.filter(profile=profile, app_post=post).delete()
    else:
        BookmarkAppPost.objects.create(profile=profile, app_post=post).save()
    return redirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='signin')
def bookmarks(request):
    bookmarks_post = BookmarkPost.objects.filter(profile=Profile.objects.filter(user=request.user).first())
    bookmarks_app_post = BookmarkAppPost.objects.filter(profile=Profile.objects.filter(user=request.user).first())
    return render(request, 'bookmarks.html',
                  context={'bookmarks_post': bookmarks_post,
                           'bookmarks_app_post': bookmarks_app_post,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def collaborations(request, user_id):
    user = User.objects.filter(id=user_id).first()
    collaborations_sent = Collaboration.objects.filter(user=user)
    collaborations_received = Collaboration.objects.filter(collaborator=Profile.objects.filter(user=user).first())
    collaborations_user = Collaboration.objects.filter(user=request.user)
    mutual = collaborations_received.intersection(collaborations_user)
    return render(request, 'collaborations.html',
                  context={'collaborations_sent': collaborations_sent,
                           'collaborations_received': collaborations_received,
                           'mutual': mutual,
                           'user_id': user_id,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def collaborate(request, user_id):
    subject = request.POST['subject']
    body = request.POST['body']
    collaboration = Collaboration.objects.filter(user=request.user,
                                                 collaborator=Profile.objects.filter(user_id=user_id).first())
    if collaboration.exists():
        collaboration.update(subject=subject, body=body)
    else:
        Collaboration.objects.create(user=request.user,
                                     collaborator=Profile.objects.filter(user_id=user_id).first(),
                                     subject=subject, body=body)
    return redirect(profile, user_id)

@login_required(login_url='signin')
def applied(request):
    posts = ApplicationForm.objects.filter(user=request.user)
    return render(request, 'applied.html',
                  context={'posts': posts,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def create_certification(request):
    name = request.POST['name']
    company = request.POST['company']
    date = request.POST['date']
    profile = Profile.objects.filter(user=request.user).first()
    if Certification.objects.filter(name=name, profile=profile).exists():
        Certification.objects.filter(name=name, profile=profile).update(name=name)
    if Certification.objects.filter(company=company, profile=profile).exists():
        Certification.objects.filter(company=company, profile=profile).update(company=company)
    if Certification.objects.filter(date=date, profile=profile).exists():
        Certification.objects.filter(date=date, profile=profile).update(date=date)
    Certification.objects.create(name=name, company=company, date=date, profile=profile).save()
    return redirect('profile', profile.user_id)

@login_required(login_url='signin')
def calendar(request):
    profile = Profile.objects.filter(user=request.user).first()

    return render(request, 'calendar.html',
                  context={
                      'profile': profile,
                      'my_profile_id': my_profile_id(request)
                  })