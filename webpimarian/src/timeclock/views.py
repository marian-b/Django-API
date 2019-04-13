from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View



from .forms import LoginForm, UserActivityForm
from .models import UserActivity

User = get_user_model()


class UsersActivityView(View):
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(UsersActivityView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        query = request.GET.get("q")
        users = User.objects.all()
        checked_in_list = []
        checked_out_list = []
        no_activity_today_users = []
        all_activity = UserActivity.objects.all()
        for u in users:
            act = all_activity.filter(user=u).today().recent()
            if act.exists():
                current_user_activity_obj = act.first()
                if current_user_activity_obj.activity == 'checkin':
                    checked_in_list.append(current_user_activity_obj.id)
                else:
                    checked_out_list.append(current_user_activity_obj.id)
            else:
                no_activity_today_users.append(u)

        checked_in_users = all_activity.filter(id__in=checked_in_list)
        checked_out_users = all_activity.filter(id__in=checked_out_list)
        all_activity = all_activity.today().recent()

        if query:
            checked_in_users = checked_in_users.filter(user__username__iexact=query)
            checked_out_users = checked_out_users.filter(user__username__iexact=query)
            all_activity = all_activity.filter(
                Q(user__username__iexact=query) |
                Q(user__first_name__iexact=query)
                )
        context = {
            "checked_in_users": checked_in_users,
            "checked_out_users": checked_out_users,
            "inactive_users": no_activity_today_users,
            "all_activity": all_activity,
            "query": query,
        }
        return render(request, "timeclock/users-activity-view.html", context)


class ActivityView(View):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ActivityView, self).dispatch(*args, **kwargs)
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseRedirect("/login/")
        if request.session.get("username"):
            username_auth = request.user.username
            username_ses = request.session.get("username")
            if username_ses == username_auth:
                username = username_auth
                context = {}
                if username:
                    form = UserActivityForm(initial={"username": username})
                    context["form"] = form
                    if request.user.is_authenticated():
                        obj = UserActivity.objects.current(request.user)
                        context['object'] = obj
        else:
            logout(request)
            return HttpResponseRedirect("/login/")
        return render(request, "timeclock/activity-view.html", context)

    def post(self, request, *args, **kwargs):
        form = UserActivityForm(request.POST)
        obj = UserActivity.objects.current(request.user)
        context = {"form": form, "object": obj}
        if form.is_valid():
            toggle = UserActivity.objects.toggle(request.user)
            context['object'] = toggle
            return HttpResponseRedirect("/")
        return render(request, "timeclock/activity-view.html", context)

class UserLoginView(View):
    def get(self, request, *args, **kwargs):
        form = LoginForm()
        context = {
            "form": form
        }
        return render(request, "timeclock/login-view.html", context)

    def post(self, request, *args, **kwargs):
        next_url = request.GET.get("next")
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                request.session['username'] = username
            if next_url:
                return HttpResponseRedirect(next_url)
            return HttpResponseRedirect("/")
        context = {"form": form}
        return render(request, "timeclock/login-view.html", context)

class UserLogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return HttpResponseRedirect("/")


def activity_view(request, *args, **kwargs):
    # get
    if request.method == 'POST':
        #post
        new_act = UserActivity.objects.create(user=request.user, activity='checkin')
    return render(request, "timeclock/activity-view.html", {})

# Create your views here.


