from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.contrib.messages.api import success
from django.db.models import Q
import json
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
    profiles = None

    my_profile = Profile.objects.get(user=request.user)

    bookmarks = BookmarkAppPost.objects.filter(profile=my_profile)

    events = []

    for bookmark in bookmarks:
        if bookmark.app_post.deadline:
            events.append({
                "title": bookmark.app_post.title,
                "start": bookmark.app_post.deadline.strftime("%Y-%m-%d"),
                "url": reverse("post", args=[bookmark.app_post.id]),
                "color": "#436850",
            })

    return render(
        request,
        "index.html",
        context={
            "posts": posts,
            "my_profile": my_profile,
            "profiles": profiles,
            "my_profile_id": my_profile_id(request),
            "events": json.dumps(events),
        },
    )

@login_required(login_url='signin')
def search(request):
    query = request.GET.get("query")

    profiles_search = Profile.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    )

    my_profile = Profile.objects.get(user=request.user)

    bookmarks = BookmarkAppPost.objects.filter(profile=my_profile)

    events = []

    for bookmark in bookmarks:
        if bookmark.app_post.deadline:
            events.append({
                "title": bookmark.app_post.title,
                "start": bookmark.app_post.deadline.strftime("%Y-%m-%d"),
                "url": reverse("post", args=[bookmark.app_post.id]),
                "color": "#436850",
            })

    return render(
        request,
        "search.html",
        context={
            "profiles_search": profiles_search,
            "query": query,
            "my_profile": my_profile,
            "my_profile_id": my_profile_id(request),
            "events": json.dumps(events),
        },
    )
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

        print(form.errors)   # Temporary for debugging

    else:
        form = ApplicationPostModelForm()

    return render(
        request,
        'create.html',
        {
            'form': form,
            'my_profile_id': my_profile_id(request),
        }
    )

@login_required(login_url='signin')
def edit_post(request, post_id):
    if request.method == 'POST':
        post = PostEditModelForm(request.POST, request.FILES, instance=Post.objects.filter(id=post_id).first())
        if post.is_valid():
            post.save()
        return redirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='signin')
def edit_app_post(request, post_id):
    if request.method == 'POST':
        post = AppPostEditModelForm(request.POST, request.FILES, instance=ApplicationPost.objects.filter(id=post_id).first())
        if post.is_valid():
            post.save()
        return redirect(request.META.get('HTTP_REFERER'))
    post = AppPostEditModelForm(instance=ApplicationPost.objects.filter(id=post_id).first())
    return render(request, 'edit_post.html',
                  context={'form': post,
                           'post_id': post_id,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def delete_post(request, post_id):
    Post.objects.get(id=post_id, profile__user=request.user).delete()
    return redirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='signin')
def delete_app_post(request, post_id):
    ApplicationPost.objects.filter(id=post_id, profile__user=request.user).first().delete()
    ApplicationForm.objects.filter(post_id=post_id).delete()
    return redirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='signin')
def edit_certification(request, certification_id):
    if request.method == 'POST':
        certification = CertificationEditModelForm(request.POST, request.FILES, instance=Certification.objects.filter(id=certification_id).first())
        if certification.is_valid():
            certification.save()
        return redirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='signin')
def delete_certification(request, certification_id):
    Certification.objects.get(id=certification_id, profile__user=request.user).delete()
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='signin')
def post(request, post_id):
    exists  = False
    deadline = False  # if the deadline has passed
    apply = True
    post = ApplicationPost.objects.filter(id=post_id).first()
    post_deadline = post.deadline

    if post.profile == Profile.objects.get(user=request.user):
        apply = False
    if post_deadline is not None:
        if post_deadline.date().__lt__(datetime.today().date()):
            deadline = True
    if ApplicationForm.objects.filter(user=request.user,  app_post_id=post_id).exists():
        exists = True
    return render(request, 'details.html',
                  context={'post': post,
                           'exists': exists,
                           'deadline': deadline,
                           'apply': apply,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def apply(request, post_id):
    profile = Profile.objects.filter(user=request.user).first()

    initial_data = {
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "email": request.user.email,
    }

    if request.method == 'POST':
        form = ApplicationFormModelForm(
            request.POST,
            request.FILES,
            initial=initial_data
        )

        if form.is_valid():
            application = form.save(commit=False)
            application.app_post = ApplicationPost.objects.filter(id=post_id).first()
            application.user = request.user
            application.save()

            return render(
                request,
                'apply.html',
                context={
                    'form': ApplicationFormModelForm(initial=initial_data),
                    'post_id': post_id,
                    'my_profile_id': my_profile_id(request),
                    'successful': True
                }
            )

    form = ApplicationFormModelForm(initial=initial_data)

    return render(
        request,
        'apply.html',
        context={
            'form': form,
            'post_id': post_id,
            'my_profile_id': my_profile_id(request)
        }
    )
@login_required(login_url='signin')
def profile(request, user_id):
    successful = False
    edit = False
    collaborated = False

    user = User.objects.filter(id=user_id).first()

    if request.user == user:
        profile = Profile.objects.filter(user=request.user).first()
        edit = True
    else:
        profile = Profile.objects.filter(user=user).first()

    if CollaborationPost.objects.filter(sender__user=request.user, receiver__user_id=user_id, accepted=False).exists():
        collaborated = True

    # logged-in user's profile (for calendar)
    my_profile = Profile.objects.get(user=request.user)

    posts = Post.objects.filter(profile=profile).order_by('-created')
    certifications = Certification.objects.filter(profile=profile).order_by('-date')

    collaboration_count = Collaboration.objects.filter(
        Q(collaborator_1=profile) | Q(collaborator_2=profile)
    ).count()

    events = []

    bookmarks = BookmarkAppPost.objects.filter(profile=my_profile)

    for bookmark in bookmarks:
        if bookmark.app_post.deadline:
            events.append({
                "title": bookmark.app_post.title,
                "start": bookmark.app_post.deadline.strftime("%Y-%m-%d"),
                "url": reverse("post", args=[bookmark.app_post.id]),
                "color": "#436850",
            })

    return render(request, 'profile.html',
                  context={
                      'profile': profile,
                      'profiles': None,
                      'posts': posts,
                      'certifications': certifications,
                      'collaboration_count': collaboration_count,
                      'edit': edit,
                      'collaborated': collaborated,
                      'successful': successful,
                      'my_profile_id': my_profile_id(request),
                      'events': json.dumps(events),
                  })
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
def profile_collaborations(request, user_id):
    user_profile = Profile.objects.get(user_id=user_id)
    request_user_profile = Profile.objects.get(user=request.user)

    def get_collaborator_ids(profile):
        return set(
            Collaboration.objects.filter(collaborator_1=profile)
            .values_list('collaborator_2_id', flat=True)
        ).union(
            Collaboration.objects.filter(collaborator_2=profile)
            .values_list('collaborator_1_id', flat=True)
        )

    # Get profile's collaborators
    collab1_ids = Collaboration.objects.filter(
        collaborator_1=user_profile
    ).values_list('collaborator_2_id', flat=True).distinct()

    collab2_ids = Collaboration.objects.filter(
        collaborator_2=user_profile
    ).values_list('collaborator_1_id', flat=True).distinct()

    all_collaborations = Profile.objects.filter(
        id__in=collab1_ids.union(collab2_ids)
    )

    # Calculate mutual collaborators with logged-in user
    my_collaborators = get_collaborator_ids(request_user_profile)

    for collab in all_collaborations:
        collab.mutual_count = len(
            my_collaborators.intersection(get_collaborator_ids(collab))
        )

    mutual_collaborations = None

    if request.user.id != user_id:
        user_collaborations = Profile.objects.filter(
            id__in=
            Collaboration.objects.filter(
                collaborator_1=request_user_profile
            ).values_list('collaborator_2_id', flat=True).distinct()
            .union(
                Collaboration.objects.filter(
                    collaborator_2=request_user_profile
                ).values_list('collaborator_1_id', flat=True).distinct()
            )
        )

        mutual_collaborations = all_collaborations.intersection(user_collaborations)

        # Add mutual count here too
        for collab in mutual_collaborations:
            collab.mutual_count = len(
                my_collaborators.intersection(get_collaborator_ids(collab))
            )

    return render(
        request,
        'profile_collabs.html',
        context={
            'all_collaborations': all_collaborations,
            'mutual_collaborations': mutual_collaborations,
            'user_id': user_id,
            'my_profile_id': my_profile_id(request)
        }
    )

@login_required(login_url='signin')
def collaborate(request, user_id):
    sender = Profile.objects.filter(user=request.user).first()
    receiver = Profile.objects.filter(user_id=user_id).first()

    subject = request.POST['subject']
    body = request.POST['body']

    CollaborationPost.objects.create(
        sender=sender,
        receiver=receiver,
        subject=subject,
        body=body
    )

    messages.success(request, "Your application has been sent.")

    return redirect('profile', user_id)

@login_required(login_url='signin')
def accept(request, user_id, post_id):
    collaboration = CollaborationPost.objects.filter(id=post_id)
    collaboration.update(accepted=True)
    Collaboration.objects.create(collaborator_1=Profile.objects.filter(user=request.user).first(),collaborator_2=Profile.objects.filter(user_id=user_id).first())
    return redirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='signin')
def applications(request):
    posts = ApplicationPost.objects.filter(profile=Profile.objects.filter(user=request.user).first())
    applied = ApplicationForm.objects.filter(user=request.user).distinct()
    return render(request, 'applications.html',
                  context={'received': posts,
                           'applied': applied,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def forms(request, post_id):
    all_forms = ApplicationForm.objects.filter(app_post_id=post_id)
    forms = []
    for form in all_forms:
        forms.append(ApplicationFormModelForm(instance=form))
    post = ApplicationPost.objects.get(id=post_id)
    return render(request, 'forms.html',
                  context={'forms': forms,
                           'form': None,
                           'post': post,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def form(request, post_id):
    post = ApplicationPost.objects.get(id=post_id)
    app_form = ApplicationForm.objects.filter(app_post_id=post_id, user=request.user).first()
    form = ApplicationFormModelForm(instance=app_form)
    return render(request, 'forms.html',
           context={'forms': None,
                    'form': form,
                    'post': post,
                    'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def collaborations(request):
    all_sent = CollaborationPost.objects.filter(sender=Profile.objects.filter(user=request.user).first())
    all_received = CollaborationPost.objects.filter(receiver=Profile.objects.filter(user=request.user).first())
    accepted = all_sent.filter(accepted=True).union(all_received.filter(accepted=True))

    sent = all_sent.filter(accepted=False)
    received = all_received.filter(accepted=False)

    return render(request, 'collaborations.html',
                  context={'sent': sent,
                           'received': received,
                           'accepted': accepted,
                           'my_profile_id': my_profile_id(request)})

@login_required(login_url='signin')
def delete_collaboration(request, post_id):
    CollaborationPost.objects.filter(id=post_id).first().delete()
    return redirect(request.META.get('HTTP_REFERER'))

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

# @login_required(login_url='signin')
# def calendar(request):
#     profile = Profile.objects.filter(user=request.user).first()
#
#     return render(request, 'calendar.html',
#                   context={
#                       'profile': profile,
#                       'my_profile_id': my_profile_id(request)
#                   })

@login_required(login_url='signin')
def calendar(request):
    profile = Profile.objects.filter(user=request.user).first()

    bookmarks = BookmarkAppPost.objects.filter(profile=profile)

    events = []

    for bookmark in bookmarks:
        if bookmark.app_post.deadline:
            events.append({
                "title": bookmark.app_post.title,
                "start": bookmark.app_post.deadline.strftime("%Y-%m-%d"),
                "url": reverse("post", args=[bookmark.app_post.id]),
                "color": "#436850",
            })

    return render(
        request,
        "calendar.html",
        {
            "profile": profile,
            "my_profile_id": my_profile_id(request),
            "events": json.dumps(events),
        },
    )