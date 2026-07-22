from django import template
from mostApp.models import Profile, Post, ApplicationPost, Collaboration, CollaborationPost

register = template.Library()

@register.filter
def get_profile_name(user_id):
    return f'{Profile.objects.filter(user_id=user_id).first().first_name} {Profile.objects.filter(user_id=user_id).first().last_name}'

@register.filter
def get_post_title(post_id):
    return f'{ApplicationPost.objects.filter(id=post_id).first().title}'

@register.filter
def get_post_profile(post_id):
    return f'{ApplicationPost.objects.filter(id=post_id).first().profile.first_name} {ApplicationPost.objects.filter(id=post_id).first().profile.last_name}'

@register.filter
def get_profile_pic_url(user_id):
    if Profile.objects.filter(user_id=user_id).first().profile_pic:
        return Profile.objects.filter(user_id=user_id).first().profile_pic.url
    else:
        return False

@register.filter
def get_collaborations(user_id):
    return CollaborationPost.objects.filter(receiver__user_id=user_id, accepted=False).exists()