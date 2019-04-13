from datetime import timedelta

from django.conf import settings
from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()

from .models import UserActivity

ACTIVITY_TIME_DELTA = getattr(settings, "ACTIVITY_TIME_DELTA", timedelta(minutes=1))

class UserActivityForm(forms.Form):
    username = forms.CharField(widget=forms.HiddenInput)
    password = forms.CharField(label='Verificare parolă', widget=forms.PasswordInput)

    def clean(self, *args, **kwargs):
        cleaned_data = super(UserActivityForm, self).clean(*args, **kwargs)
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        qs = User.objects.filter(username__iexact=username)
        if not qs.exists() or qs.count() != 1:
            raise forms.ValidationError("Parolă incorectă")
        else:
            user_obj = qs.first()
            current = UserActivity.objects.current(user_obj)
            if current:
                actual_obj_time = current.timestamp
                the_delta = ACTIVITY_TIME_DELTA
                diff = the_delta + actual_obj_time
                now = timezone.now()
                if diff > now:
                    raise forms.ValidationError("Trebuie să așteptați {time} pentru această acțiune".format(time=the_delta))
            if not user_obj.check_password(password):
                raise forms.ValidationError("Parolă incorectă")
        return cleaned_data

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self, *args, **kwargs):
        cleaned_data = super(LoginForm, self).clean(*args, **kwargs)
        username = cleaned_data.get('Utilizator')
        password = cleaned_data.get('Parolă')
        qs = User.objects.filter(username__iexact=username)
        if not qs.exists() or qs.count() != 1:
            raise forms.ValidationError("Nume de utilizator/parolă incorectă")
        else:
            user_obj = qs.first()
            if not user_obj.check_password(password):
                raise forms.ValidationError("Nume de utilizator/parolă incorectă")
        return cleaned_data

    # def clean_username(self, *args, **kwargs):
    #     username = self.cleaned_data['username'] #.get('username')
    #     qs = User.objects.filter(username__iexact=username)
    #     if not qs.exits() or qs.count() != 1:
    #         raise forms.ValidationError("Nume de utilizator/parola incorecta")
    #     return username
    #
    # def clean_password(self, *args, **kwargs):
    #     username = self.cleaned_data['username']  # .get('username')
    #     password = self.cleaned_data['password']
    #     qs = User.objects.filter(username__iexact=username)
    #     if qs.exits() and qs.count() == 1:
    #         user.obj = qs.first()
    #         if not user_obj.check_password(password):
    #             raise forms.ValidationError("Nume de utilizator/parola incorecta")
    #         return password
    #     else:
    #         raise forms.ValidationError("Nume de utilizator/parola incorecta")

