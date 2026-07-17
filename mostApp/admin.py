from django.contrib import admin

from mostApp.models import *

# Register your models here.

class ProfilePostInline(admin.TabularInline):
    model = Post
    extra = 0

class ProfileApplicationPostInline(admin.TabularInline):
    model = ApplicationPost
    extra = 0

class ProfileCertificationInline(admin.TabularInline):
    model = Certification
    extra = 0


class  ProfileAdmin(admin.ModelAdmin):
    inlines = [ProfilePostInline, ProfileApplicationPostInline, ProfileCertificationInline]


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Post)
admin.site.register(ApplicationPost)
admin.site.register(Certification)
admin.site.register(CollaborationPost)
admin.site.register(BookmarkPost)
admin.site.register(BookmarkAppPost)
admin.site.register(Tag)