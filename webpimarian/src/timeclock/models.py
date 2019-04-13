from datetime import timedelta, datetime, time
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from django.utils import timezone

ACTIVITY_TIME_DELTA = getattr(settings, "ACTIVITY_TIME_DELTA", timedelta(minutes=1))

# https://docs.djangoproject.com/en/1.10/ref/exceptions/#django.core.exceptions.Validation.Error

# Create your models here.

# 1. Users details
# 2. Daily Time Clock app
# 3. In and Out per Day / Users

# class UserDayTime(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL)
#     today = models.DateField(default=timezone.now)


USER_ACTIVITY_CHOICES = (
    ('checkin', 'Check In'),
    ('checkout', 'Check Out'),
)

class UserActivityQuerySet(models.query.QuerySet):
    def recent(self):
        return self.order_by("-timestamp")

    def today(self):
        now = timezone.now()
        today_start = timezone.make_aware(datetime.combine(now, time.min))
        today_end = timezone.make_aware(datetime.combine(now, time.max))
        return self.filter(timestamp__gte=today_start).filter(timestamp__lte=today_end)

    def checkin(self,):
        return self.filter(activity='checkin')

    def checkout(self,):
        return self.filter(activity='checkout')

    def current(self, user=None):
        if user is None:
            return self
        return self.filter(user=user).order_by('-timestamp').first()

class UserActivityManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return UserActivityQuerySet(self.model, using=self._db)

    def checkin(self):
        return self.get_queryset().checkin()

    def checkout(self):
        return self.get_queryset().checkout()

    def current(self, user=None):
        if user is None:
            return None
        current_obj = self.get_queryset().current(user)
        return current_obj

    def toggle(self, user=None):
        if user is None:
            return None
        last_item = self.current(user)
        activity = "checkin"
        if last_item is not None:
            now = timezone.now()
            diff = last_item.timestamp + ACTIVITY_TIME_DELTA
            if diff > now:
                return None
            #if last_item.timestamp <= datetime.datetime.now():
            #    pass
            if last_item.activity == "checkin":
                activity = "checkout"
        obj = self.model(
                user=user,
                activity=activity
            )
        obj.save()
        return obj


class UserActivity(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    activity = models.CharField(max_length=120, default='checkin', choices=USER_ACTIVITY_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = UserActivityManager()

    def __unicode__(self):
        return str(self.activity)

    def __str__(self):
        return str(self.activity)

    class Meta:
        verbose_name = "activitate utilizator"
        verbose_name_plural = "activitati utilizator"

    @property
    def next_activity(self):
        next = "Conectare"
        if self.activity == 'checkin':
            next = "Deconectare"
        return next

    @property
    def current(self):
        current = "Deconectat"
        if self.activity == 'checkin':
            current = "Conectat"
        return current



    def clean(self, *args, **kwargs):
        if self.user:
            user_activites = UserActivity.objects.exclude(
                id=self.id
            ).filter(
                user=self.user
            ).order_by('-timestamp')
            if user_activites.exists():
                recent_= user_activites.first()
                if self.activity == recent_.activity:
                    message = "%s nu este o activitate validă pentru acest utilizator" %(self.get_activity_display())
                    raise ValidationError(message)
            else:
                if self.activity != "checkin":
                    message = "%s nu este o primă activitate validă pentru acest utilizator" %(self.get_activity_display())
                    raise ValidationError(message)

        return super(UserActivity, self).clean(*args, **kwargs)


