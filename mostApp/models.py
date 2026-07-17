from cProfile import label

from django.contrib.auth.models import User
from django.db import models

# Create your models here.


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    occupation = models.CharField(max_length=200, null=True, blank=True)
    contact = models.CharField(max_length=100, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    profile_pic = models.ImageField(upload_to='profiles/', null=True, blank=True)
    about_me = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

class Tag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.name}'

class Post(models.Model):
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.profile.first_name} {self.profile.last_name} {self.content}'

class ApplicationPost(models.Model):
    title = models.CharField(max_length=100)
    short_description = models.TextField()
    long_description = models.TextField()  # see more section
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(null=True, blank=True)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.profile.first_name} {self.profile.last_name} {self.title}'

class ApplicationForm(models.Model):
    UNI_CHOICES = [
        ('ARH', 'Faculty of Architecture'),
        ('CVL', 'Faculty of Civil Engineering'),
        ('ECN', 'Faculty of Economics'),
        ('MCH', 'Faculty of Mechanical Engineering'),
        ('MED', 'Faculty of Medicine'),
        ('PED', 'St. Kliment Ohridski Faculty of Law Pedagogy'),
        ('LAW', 'Faculty of Law "Justinian Primus"'),
        ('PMF', 'Faculty of Natural Science and Mathematics'),
        ('DENT', 'Faculty of Dentistry'),
        ('TMF', 'Faculty of Technology and Metallurgy'),
        ('VET', 'Faculty of Veterinary Medicine'),
        ('DTFI', 'Faculty of Design and Technologies of Furniture and Interior'),
        ('DRM', 'Faculty of Dramatics Arts'),
        ('FEIT', 'Faculty of Electrical Engineering and Information Technologies'),
        ('ASF', 'Faculty of Agricultural Science and Food'),
        ('FCSE', 'Faculty of Computer Science and Engineering'),
        ('FA', 'Faculty of Fine Arts'),
        ('MUS', 'Faculty of Music'),
        ('PESH', 'Faculty of Physical Education, Sport and Health'),
        ('FSLE', '"Hans Em" Faculty of Forest Sciences, Landscape Architecture and Environment Engineering'),
        ('PHAR', 'Faculty of Pharmacy'),
        ('PHS', 'Faculty of Philosophy'),
        ('PHL', '"Blaze Koneski" Faculty of Philology'),
    ]
    EDUCATION_CHOICES = [
        ('SE','Secondary Education'),
        ('PE', 'Post-secondary Education'),
        ('BD', 'Bachelor\'s Degree'),
        ('MD', 'Master\'s Degree'),
        ('DD', 'Doctorate\'s Degree'),
    ]
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    education = models.CharField(max_length=2, choices=EDUCATION_CHOICES)
    faculty = models.CharField(max_length=4, choices=UNI_CHOICES)
    motivational_letter = models.TextField()
    cv = models.FileField(upload_to='applications/cv')
    post_id = models.CharField(max_length=100, null=True, blank=True)
    app_post = models.ForeignKey(ApplicationPost, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Certification(models.Model):
    name = models.TextField()
    company = models.TextField()
    date = models.DateTimeField()
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.profile.first_name} {self.profile.last_name} {self.name}'

class BookmarkPost(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.profile.first_name} {self.profile.last_name} bookmarked {self.post.profile.first_name} {self.post.profile.last_name}\'s post'

class BookmarkAppPost(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    app_post = models.ForeignKey(ApplicationPost, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.profile.first_name} {self.profile.last_name} bookmarked {self.app_post.title}'

class ProfileAppliedPost(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    post = models.ForeignKey(ApplicationPost, on_delete=models.CASCADE)
    form = models.ForeignKey(ApplicationForm, on_delete=models.CASCADE)

class CollaborationPost(models.Model):
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="sent_collaboration")
    receiver = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="received_collaboration")
    subject = models.CharField(max_length=100)
    body = models.TextField()
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return f'{Profile.objects.filter(user=self.sender).first()} sent collaboration to {self.receiver.first_name}'

class Collaboration(models.Model):
    collaborator_1 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="collaboration_sender", null=True, blank=True)
    collaborator_2 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="collaboration_receiver", null=True, blank=True)

    def __str__(self):
        return f'{Profile.objects.filter(user=self.collaborator_1).first()} and {self.collaborator_2.first_name} collaborated'