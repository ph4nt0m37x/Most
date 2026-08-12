import random
import networkx as nx
from _ssl import Certificate
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import json
from django.http import JsonResponse
from django.utils.dateparse import parse_date

from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages, auth
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, datetime

from mostApp.forms import *
from mostApp.models import *
from mostApp.recommendations import recommend_by_influence


# Create your views here.


def get_collaborator_ids(profile):
    return set(
        Collaboration.objects.filter(collaborator_1=profile)
        .values_list('collaborator_2_id', flat=True)
    ).union(
        Collaboration.objects.filter(collaborator_2=profile)
        .values_list('collaborator_1_id', flat=True)
    )


def get_people_you_may_know(request, user_id):
    graph = nx.Graph()
    graph.add_nodes_from(list(Profile.objects.all().values_list('id', flat=True)))
    graph.add_edges_from(list(Collaboration.objects.all().values_list('collaborator_1', 'collaborator_2')))

    people = recommend_by_influence(graph, user_id)

    friends = Collaboration.objects.filter(collaborator_1__id=user_id).values_list('collaborator_2', flat=True).union(
        Collaboration.objects.filter(collaborator_2__id=user_id).values_list('collaborator_1', flat=True)
    )

    profiles = Profile.objects.all().values_list('id', flat=True)

    if len(people) < 3:
        if len(profiles) > 3:
            allowed_numbers = [i for i in range(1, len(profiles) + 1) if
                               i not in friends and i != user_id and i not in people]
            if len(allowed_numbers) >= 3:
                result = random.sample(allowed_numbers, 3)
                for i in range(0, 3 - len(people)):
                    people.append(Profile.objects.filter(pk=result[i]).first().id)
            else:
                for i in range(0, len(allowed_numbers)):
                    people.append(Profile.objects.filter(pk=allowed_numbers[i]).first().id)
        else:
            for i in range(0, len(profiles)):
                if i not in friends and i != user_id and i not in people:
                    people.append(Profile.objects.filter(pk=profiles[i]).first().id)

    if len(people) > 3:
        people = people[:3]

    request.session['people'] = people


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
                get_people_you_may_know(request, new_profile.id)
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
            get_people_you_may_know(request, Profile.objects.filter(user=user).first().id)
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
    thirty_days_ago = timezone.now() - timedelta(days=30)
    posts = Post.objects.filter(created__gte=thirty_days_ago).order_by('-created')

    people_ids = request.session['people']
    people = []
    for id in people_ids:
        people.append(Profile.objects.filter(id=id).first())

    my_profile = Profile.objects.get(user=request.user)

    my_collaborators = get_collaborator_ids(my_profile)

    for person in people:
        person.mutual_count = len(
            my_collaborators.intersection(get_collaborator_ids(person))
        )

    bookmarks = BookmarkAppPost.objects.filter(profile=my_profile)

    events = []

    for bookmark in bookmarks:
        if bookmark.app_post.deadline:
            events.append({
                "title": bookmark.app_post.title,
                "start": bookmark.app_post.deadline.strftime("%Y-%m-%d"),
                "url": reverse("application_post", args=[bookmark.app_post.id]),
                "color": "#436850",
            })

    return render(
        request,
        "index.html",
        context={
            "posts": posts,
            "my_profile": my_profile,
            "people": people,
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

    people_ids = request.session['people']
    people = []
    for id in people_ids:
        people.append(Profile.objects.filter(id=id).first())

    my_profile = Profile.objects.get(user=request.user)

    my_collaborators = get_collaborator_ids(my_profile)

    for profile in profiles_search:
        profile.mutual_count = len(
            my_collaborators.intersection(get_collaborator_ids(profile))
        )

    for person in people:
        person.mutual_count = len(
            my_collaborators.intersection(get_collaborator_ids(person))
        )

    bookmarks = BookmarkAppPost.objects.filter(profile=my_profile)

    events = []

    for bookmark in bookmarks:
        if bookmark.app_post.deadline:
            events.append({
                "title": bookmark.app_post.title,
                "start": bookmark.app_post.deadline.strftime("%Y-%m-%d"),
                "url": reverse("application_post", args=[bookmark.app_post.id]),  # Change this to your application post URL name if needed
                "color": "#436850",
            })

    return render(
        request,
        "search.html",
        context={
            "profiles_search": profiles_search,
            "query": query,
            "people": people,
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
                           'clear': True,
                           'my_profile_id': my_profile_id(request)})


@login_required(login_url='signin')
def browse_filter(request):
    date_filter = request.GET.get('date_filter')
    filter_option = request.GET.getlist('filter')
    posts = ApplicationPost.objects.all()
    if date_filter.__contains__('-'):
        thirty_days_ago = parse_date(date_filter) - timedelta(days=30)
        posts = ApplicationPost.objects.filter(created__date__lte=date_filter, created__date__gte=thirty_days_ago).order_by('-created')
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
                           'clear': True,
                           'tags': tags,
                           'filter': filter,
                           'date_filter': date_filter,
                           'my_profile_id': my_profile_id(request)})


@login_required(login_url='signin')
def create_post(request):
    content = request.POST.get('content')
    image = request.FILES.get("file")
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

            return render(
                request,
                'create.html',
                {
                    'form': form,
                    'my_profile_id': my_profile_id(request),
                    'successful': True,
                }
            )

        print(form.errors)

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
        post = get_object_or_404(Post, id=post_id)
        form = PostEditModelForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
        return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='signin')
def edit_app_post(request, post_id):
    app_post = get_object_or_404(ApplicationPost, id=post_id)
    if request.method == 'POST':
        post = AppPostEditModelForm(request.POST, request.FILES, instance=app_post)
        form = ApplicationPostModelForm(request.POST, request.FILES)
        if post.is_valid():
            post.save()
        return render(
            request,
            "edit_post.html",
            {
                "form": form,
                "post_id": post_id,
                "my_profile_id": my_profile_id(request),
                "successful": True,
            }
        )
    post = AppPostEditModelForm(instance=app_post)
    return render(request, 'edit_post.html',
                  context={'form': post,
                           'post_id': post_id,
                           'my_profile_id': my_profile_id(request)})


@login_required(login_url='signin')
def delete_post(request, post_id):
    Post.objects.filter(id=post_id).first().delete()
    if request.path.find('details') != -1:
        return redirect('post', post_id=post_id)
    else:
        return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='signin')
def delete_app_post(request, post_id):
    ApplicationPost.objects.filter(id=post_id, profile__user=request.user).first().delete()
    ApplicationForm.objects.filter(post_id=post_id).delete()
    if request.path.find('details') != -1:
        return redirect('application_post', post_id=post_id)
    else:
        return redirect(request.META.get('HTTP_REFERER'))

@login_required(login_url='signin')
def edit_certification(request, certification_id):
    if request.method == 'POST':
        cert = get_object_or_404(Certification, id=certification_id)
        certification = CertificationEditModelForm(request.POST, request.FILES, instance=cert)
        if certification.is_valid():
            certification.save()
        return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='signin')
def delete_certification(request, certification_id):
    get_object_or_404(Certification, id=certification_id, profile__user=request.user).delete()
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='signin')
def application_post(request, post_id):
    exists  = False
    deadline = False  # if the deadline has passed
    apply = True
    post = ApplicationPost.objects.filter(id=post_id).first()
    if post:
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
                       'deleted': post is None,
                       'app_post': True,
                       'my_profile_id': my_profile_id(request)})


@login_required(login_url='signin')
def post(request, post_id):
    post = Post.objects.filter(id=post_id).first()

    return render(request, 'details.html',
                  context={'post': post,
                           'app_post': False,
                           'deleted': post is None,
                           'my_profile_id': my_profile_id(request)})


@login_required(login_url='signin')
def apply(request, post_id):
    profile = Profile.objects.filter(user=request.user).first()

    initial_data = {
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "email": request.user.username,
    }

    if request.method == 'POST':
        form = ApplicationFormModelForm(
            request.POST,
            request.FILES,
            initial=initial_data
        )

        if form.is_valid():
            application = form.save(commit=False)
            application.app_post = get_object_or_404(ApplicationPost, id=post_id)
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

    user = get_object_or_404(User, id=user_id)

    people_ids = request.session['people']
    people=[]
    for id in people_ids:
        people.append(Profile.objects.filter(id=id).first())

    if request.user == user:
        profile = Profile.objects.filter(user=request.user).first()
        edit = True
    else:
        profile = Profile.objects.filter(user=user).first()

    if CollaborationPost.objects.filter(sender__user=request.user, receiver__user_id=user_id, status='PEND').exists():
        collaborated = True

    # logged-in user's profile (for calendar)
    my_profile = Profile.objects.get(user=request.user)

    posts = Post.objects.filter(profile=profile).order_by('-created')
    certifications = Certification.objects.filter(profile=profile).order_by('-date')

    collaboration_count = Collaboration.objects.filter(
        Q(collaborator_1=profile) | Q(collaborator_2=profile)
    ).count()

    my_collaborators = get_collaborator_ids(profile)

    for person in people:
        person.mutual_count = len(
            my_collaborators.intersection(get_collaborator_ids(person))
        )

    events = []

    bookmarks = BookmarkAppPost.objects.filter(profile=my_profile)

    for bookmark in bookmarks:
        if bookmark.app_post.deadline:
            events.append({
                "title": bookmark.app_post.title,
                "start": bookmark.app_post.deadline.strftime("%Y-%m-%d"),
                "url": reverse("application_post", args=[bookmark.app_post.id]),
                "color": "#436850",
            })

    return render(request, 'profile.html',
                  context={
                      'profile': profile,
                      'people': people,
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
                                       instance=Profile.objects.filter(user=request.user).first())
        if user.is_valid() or profile.is_valid():
            print(request.user.id)
            user.save()
            profile.save()
        return redirect('profile', request.user.pk)
    user = UserEditModelForm(instance=request.user)
    profile = ProfileEditModelForm(instance=Profile.objects.filter(user=request.user).first())
    return render(request, 'edit.html',
                  context={'user': user,
                           'profile': profile,
                           'my_profile_id': my_profile_id(request)})


@login_required(login_url='signin')
def bookmark_post(request, post_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    profile = Profile.objects.filter(user=request.user).first()
    post = get_object_or_404(Post, id=post_id)

    bookmarked = False
    if BookmarkPost.objects.filter(profile=profile, post=post).exists():
        BookmarkPost.objects.filter(profile=profile, post=post).delete()
    else:
        BookmarkPost.objects.create(profile=profile, post=post)
        bookmarked = True

    return JsonResponse({'bookmarked': bookmarked})


@login_required(login_url='signin')
def bookmark_app_post(request, post_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    profile = Profile.objects.filter(user=request.user).first()
    post = get_object_or_404(ApplicationPost, id=post_id)

    bookmarked = False
    if BookmarkAppPost.objects.filter(profile=profile, app_post=post).exists():
        BookmarkAppPost.objects.filter(profile=profile, app_post=post).delete()
    else:
        BookmarkAppPost.objects.create(profile=profile, app_post=post).save()
        bookmarked = True

    return JsonResponse({'bookmarked': bookmarked})


@login_required(login_url='signin')
def bookmarks(request):
    bookmarks_post = BookmarkPost.objects.filter(profile=Profile.objects.filter(user=request.user).first()).order_by('-post__created')
    bookmarks_app_post = BookmarkAppPost.objects.filter(profile=Profile.objects.filter(user=request.user).first()).order_by('-app_post__created')
    return render(request, 'bookmarks.html',
                  context={'bookmarks_post': bookmarks_post,
                           'bookmarks_app_post': bookmarks_app_post,
                           'my_profile_id': my_profile_id(request)})


@login_required(login_url='signin')
def profile_collaborations(request, user_id):
    user_profile = get_object_or_404(Profile, user_id=user_id)
    request_user_profile = Profile.objects.get(user=request.user)

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
            'my_profile': request_user_profile == user_profile,
            'my_profile_id': my_profile_id(request)
        }
    )


@login_required(login_url='signin')
def collaborate(request, user_id):
    sender = Profile.objects.filter(user=request.user).first()
    receiver = get_object_or_404(Profile, user_id=user_id)

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
    sender = Profile.objects.filter(user=request.user).first()
    receiver = get_object_or_404(Profile, user_id=user_id)

    collaboration = get_object_or_404(CollaborationPost, id=post_id)
    collaboration.status = 'ACC'
    collaboration.save()

    if not Collaboration.objects.filter(Q(collaborator_1=sender, collaborator_2=receiver)
                                        | Q(collaborator_1=receiver,collaborator_2=sender)).exists():
        Collaboration.objects.create(collaborator_1=sender, collaborator_2=receiver)
        get_people_you_may_know(request, sender.id)

    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='signin')
def deny(request, post_id):
    collaboration = get_object_or_404(CollaborationPost, id=post_id)
    collaboration.status = 'DEN'
    collaboration.save()
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='signin')
def applications(request):
    posts = ApplicationPost.objects.filter(profile=Profile.objects.filter(user=request.user).first()).order_by('-created')
    applied = ApplicationForm.objects.filter(user=request.user).distinct().order_by('-app_post__created')
    return render(request, 'applications.html',
                  context={'received': posts,
                           'applied': applied,
                           'my_profile_id': my_profile_id(request)})


@login_required(login_url='signin')
def forms(request, post_id):
    all_forms = ApplicationForm.objects.filter(app_post_id=post_id)
    forms = []
    for form in all_forms:
        forms.append(ApplicationFormModelForm(instance=form, apply=False))
    post = ApplicationPost.objects.filter(id=post_id).first()
    return render(request, 'forms.html',
                  context={'forms': forms,
                           'form': None,
                           'post': post,
                           'my_profile_id': my_profile_id(request)})


@login_required(login_url='signin')
def form(request, post_id):
    post = get_object_or_404(ApplicationPost, id=post_id)
    app_form = get_object_or_404(ApplicationForm, app_post_id=post_id, user=request.user)
    form = ApplicationFormModelForm(instance=app_form, apply=False)
    status = app_form.get_status_display()
    return render(request, 'forms.html',
           context={'forms': None,
                    'form': form,
                    'status': status,
                    'post': post,
                    'my_profile_id': my_profile_id(request)})


@login_required(login_url='signin')
def accept_application(request, form_id):
    form = get_object_or_404(ApplicationForm, id=form_id)
    form.status = 'ACC'
    form.save()
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='signin')
def deny_application(request, form_id):
    form = get_object_or_404(ApplicationForm, id=form_id)
    form.status = 'DEN'
    form.save()
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='signin')
def collaborations(request):
    all_sent = CollaborationPost.objects.filter(sender=Profile.objects.filter(user=request.user).first())
    all_received = CollaborationPost.objects.filter(receiver=Profile.objects.filter(user=request.user).first())

    sent_accepted = all_sent.filter(status='ACC').order_by('-created')
    received_accepted = all_received.filter(status='ACC').order_by('-created')

    sent = all_sent.filter(Q(status='PEND') | Q(status='DEN')).order_by('-created')
    received = all_received.filter(Q(status='PEND') | Q(status='DEN')).order_by('-created')

    return render(request, 'collaborations.html',
                  context={'sent': sent,
                           'received': received,
                           'sent_accepted': sent_accepted,
                           'received_accepted': received_accepted,
                           'my_profile_id': my_profile_id(request)})


@login_required(login_url='signin')
def delete_collaboration(request, post_id):
    get_object_or_404(CollaborationPost, id=post_id).delete()
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
                "url": reverse("application_post", args=[bookmark.app_post.id]),
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