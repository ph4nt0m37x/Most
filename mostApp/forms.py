from django import forms
from django.utils.safestring import mark_safe

from mostApp.models import *


class ApplicationPostModelForm(forms.ModelForm):
    tag = forms.ModelChoiceField(
        queryset=Tag.objects.all(),
        empty_label="Select a tag.",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    def __init__(self, *args, **kwargs):
        super(ApplicationPostModelForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    class Meta:
        model = ApplicationPost
        exclude = ['profile', 'created', 'apply_form']
        widgets = {
            'deadline':
                forms.DateTimeInput(
                    attrs={
                        'class': 'form-control', 'data-target': '#deadline', 'type': 'datetime-local',
                    }),
            'title': forms.TextInput(
                attrs={
                    'placeholder': 'Write a title...'
                }
            ),
            'short_description': forms.Textarea(
                attrs={
                    'placeholder': 'Write a short description...'
                }
            ),
            'long_description': forms.Textarea(
                attrs={
                    'placeholder': 'Describe your post...'
                }
            ),
        }

class CustomCvWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        if value:
            file = value.name.split('/')[-1]
            return mark_safe(f'<a href="{value.url}">{file}</a>')
        return mark_safe('<span>No file.</span>')

class ApplicationFormModelForm(forms.ModelForm):
    education = forms.ChoiceField(
        choices=ApplicationForm.EDUCATION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    faculty = forms.ChoiceField(
        choices=ApplicationForm.UNI_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    motivational_letter = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Write your motivational letter here...'
        })
    )

    def __init__(self, *args, **kwargs):
        super(ApplicationFormModelForm, self).__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            for field_name, field in self.fields.items():
                field.disabled = True

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = field.widget.attrs.get('class', 'form-control')

        self.fields['cv'].widget = CustomCvWidget()
        self.fields['cv'].label = 'CV'

    class Meta:
        model = ApplicationForm
        exclude = ['app_post', 'post_id', 'user', 'status']

class ProfileEditModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProfileEditModelForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    class Meta:
        model = Profile
        exclude = ['user']

class UserEditModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserEditModelForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    class Meta:
        model = User
        fields = ['email']

class PostEditModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PostEditModelForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    class Meta:
        model = Post
        fields = ['content']

class AppPostEditModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AppPostEditModelForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    class Meta:
        model = ApplicationPost
        exclude = ['profile', 'created']
        widgets = {
            'deadline':
                forms.DateTimeInput(
                    attrs={
                        'class': 'form-control', 'data-target': '#deadline', 'type': 'datetime-local',
                    })
        }

class CertificationEditModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CertificationEditModelForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    class Meta:
        model = Certification
        exclude = ['profile']
