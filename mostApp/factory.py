import os
import sys
import random
from django.utils import timezone

import django

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'most.settings')
django.setup()

from django.contrib.auth.models import User
from faker import Faker

from mostApp.models import Profile, Post, Tag, ApplicationPost, Certification

fake = Faker()


def generate_profile_data(count=10):
    for _ in range(count):
        unique_email = fake.unique.email()

        user = User.objects.create_user(
            username=unique_email,
            email=unique_email,
            password='password1!'
        )
        user.is_active = True
        user.save()
        Profile.objects.create(
            user=user,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            occupation=fake.company(),
            contact=fake.email(),
            website=fake.url(),
            profile_pic=fake.image_url(),
            about_me=fake.text(),
        )


def generate_tag_data(count=5):
    for _ in range(count):
        Tag.objects.create(
            name=fake.word(),
        )


def generate_post_data(count=10):
    for _ in range(count):
        Post.objects.create(
            profile=Profile.objects.filter(id=random.randint(1, 10)).first(),
            content=fake.text(),
            image=fake.image_url(),
            location=fake.city(),
            created=fake.date_time_between(start_date='-30d', end_date='now', tzinfo=timezone.get_current_timezone()),
        )


def generate_app_post_data(count=10):
    for _ in range(count):
        ApplicationPost.objects.create(
            title=fake.sentence(),
            short_description=fake.text(),
            long_description=fake.text(),
            profile=Profile.objects.filter(id=random.randint(1, 10)).first(),
            created=fake.date_time_between(start_date='-30d', end_date='now', tzinfo=timezone.get_current_timezone()),
            deadline=fake.date_time_between(start_date='-30d', end_date='+30d', tzinfo=timezone.get_current_timezone()),
            tag=Tag.objects.filter(id=random.randint(1, 5)).first()
        )


def generate_certification_data(count=10):
    for _ in range(count):
        Certification.objects.create(
            name=fake.word(),
            company=fake.company(),
            date=fake.date_time_between(start_date='-30d', end_date='now', tzinfo=timezone.get_current_timezone()),
            profile=Profile.objects.filter(id=random.randint(1, 10)).first(),
        )


if __name__ == '__main__':
    generate_tag_data(5)
    generate_profile_data(7)
    generate_post_data(10)
    generate_app_post_data(10)
    generate_certification_data(10)
