from django import forms

from mostApp.models import *


class ApplicationPostModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ApplicationPostModelForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    class Meta:
        model = ApplicationPost
        exclude = ['profile', 'created', 'apply_form']
        widgets = {'deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'data-target': '#deadline'})}

class ApplicationFormModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ApplicationFormModelForm, self).__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            for field_name, field in self.fields.items():
                field.disabled = True

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    class Meta:
        model = ApplicationForm
        exclude = ['app_post', 'post_id', 'user']

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