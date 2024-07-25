from datetime import timedelta

# Importing necessary Django views and models
from django.db.models import Count
from django.utils.timezone import now
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DetailView,
    DeleteView,
    View,
)
from adminPortal.models import EventRegistration

# Importing additional Django utilities
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .forms import LoginForm, EventForm, EventImageForm, EventAgendaForm, EventCreateMultiForm
from .models import (
    EventCategory,
    Event,
    EventMember,
    EventUserWishList,
    UserCoin
)

# Function to check if the user is an admin
def is_admin(user):
    return user.is_staff

# View to display registration details
@login_required
@user_passes_test(is_admin)
def registration_details_view(request):
    registrations = EventRegistration.objects.registration_details()
    context = {
        'registrations': registrations,
    }
    return render(request, 'events/registration_details.html', context)

# View to display user details for a specific event
@login_required
@user_passes_test(is_admin)
def event_user_details_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    registrations = EventRegistration.objects.filter(event=event)
    context = {
        'event': event,
        'registrations': registrations,
    }
    return render(request, 'events/event_user_details.html', context)

# Event category list view
class EventCategoryListView(LoginRequiredMixin, ListView):
    login_url = 'login'
    model = EventCategory
    template_name = 'events/event_category.html'
    context_object_name = 'event_category'


# Event category create view
class EventCategoryCreateView(LoginRequiredMixin, CreateView):
    login_url = 'login'
    model = EventCategory
    fields = ['name', 'code', 'image']
    template_name = 'events/create_event_category.html'
    success_url = reverse_lazy('event-category-list')

    def form_valid(self, form):
        form.instance.created_user = self.request.user
        form.instance.updated_user = self.request.user
        return super().form_valid(form)


# Event category update view
class EventCategoryUpdateView(LoginRequiredMixin, UpdateView):
    login_url = 'login'
    model = EventCategory
    fields = ['name', 'code', 'image']
    template_name = 'events/edit_event_category.html'
    success_url = reverse_lazy('event-category-list')


# Event category delete view
class EventCategoryDeleteView(LoginRequiredMixin, DeleteView):
    login_url = 'login'
    model = EventCategory
    template_name = 'events/event_category_delete.html'
    success_url = reverse_lazy('event-category-list')


# View to create an event
@login_required(login_url='login')
def create_event(request):
    event_form = EventForm()
    event_image_form = EventImageForm()
    event_agenda_form = EventAgendaForm()
    catg = EventCategory.objects.all()
    if request.method == 'POST':
        event_form = EventForm(request.POST)
        event_image_form = EventImageForm(request.POST, request.FILES)
        event_agenda_form = EventAgendaForm(request.POST)
        if event_form.is_valid() and event_image_form.is_valid() and event_agenda_form.is_valid():
            ef = event_form.save()
            Event.created_updated(Event, request)
            event_image_form.save(commit=False)
            event_image_form.event_form = ef
            event_image_form.save()

            event_agenda_form.save(commit=False)
            event_agenda_form.event_form = ef
            event_agenda_form.save()
            return redirect('event-list')
    context = {
        'form': event_form,
        'form_1': event_image_form,
        'form_2': event_agenda_form,
        'ctg': catg
    }
    return render(request, 'events/create_event.html', context)


# Event create view using MultiModelForm
class EventCreateView(LoginRequiredMixin, CreateView):
    login_url = 'login'
    form_class = EventCreateMultiForm
    template_name = 'events/create_event.html'
    success_url = reverse_lazy('event-list')

    def form_valid(self, form):
        evt = form['event'].save()
        event_image = form['event_image'].save(commit=False)
        event_image.event = evt
        event_image.save()

        event_agenda = form['event_agenda'].save(commit=False)
        event_agenda.event = evt
        event_agenda.save()

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ctg'] = EventCategory.objects.all()
        return context


# Event list view
class EventListView(LoginRequiredMixin, ListView):
    login_url = 'login'
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'


# Event update view
class EventUpdateView(LoginRequiredMixin, UpdateView):
    login_url = 'login'
    model = Event
    fields = ['category', 'name', 'uid', 'description', 'scheduled_status', 'venue', 'start_date', 'end_date',
              'location', 'maximum_attende', 'status']
    template_name = 'events/edit_event.html'


# Event detail view
class EventDetailView(LoginRequiredMixin, DetailView):
    login_url = 'login'
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'


# Event delete view
class EventDeleteView(LoginRequiredMixin, DeleteView):
    login_url = 'login'
    model = Event
    template_name = 'events/delete_event.html'
    success_url = reverse_lazy('event-list')


# View to add an event member
class AddEventMemberCreateView(LoginRequiredMixin, CreateView):
    login_url = 'login'
    model = EventMember
    fields = ['event', 'user', 'status']
    template_name = 'events/add_event_member.html'

    def form_valid(self, form):
        form.instance.created_user = self.request.user
        form.instance.updated_user = self.request.user
        return super().form_valid(form)


# View to list joined events
class JoinEventListView(LoginRequiredMixin, ListView):
    login_url = 'login'
    model = EventMember
    template_name = 'events/joinevent_list.html'
    context_object_name = 'eventmember'


# View to remove an event member
class RemoveEventMemberDeleteView(LoginRequiredMixin, DeleteView):
    login_url = 'login'
    model = EventMember
    template_name = 'events/remove_event_member.html'
    success_url = reverse_lazy('join-event-list')


# View to list events in the user's wish list
class EventUserWishListView(LoginRequiredMixin, ListView):
    login_url = 'login'
    model = EventUserWishList
    template_name = 'events/event_user_wish_list.html'
    context_object_name = 'eventwish'


# View to add an event to the user's wish list
class AddEventUserWishListCreateView(LoginRequiredMixin, CreateView):
    login_url = 'login'
    model = EventUserWishList
    fields = ['event', 'user', 'status']
    template_name = 'events/add_event_user_wish.html'

    def form_valid(self, form):
        form.instance.created_user = self.request.user
        form.instance.updated_user = self.request.user
        return super().form_valid(form)


# View to remove an event from the user's wish list
class RemoveEventUserWishDeleteView(LoginRequiredMixin, DeleteView):
    login_url = 'login'
    model = EventUserWishList
    template_name = 'events/remove_event_user_wish.html'
    success_url = reverse_lazy('event-wish-list')


# View to update event status
class UpdateEventStatusView(LoginRequiredMixin, UpdateView):
    login_url = 'login'
    model = Event
    fields = ['status']
    template_name = 'events/update_event_status.html'


# View to list completed events
class CompleteEventList(LoginRequiredMixin, ListView):
    login_url = 'login'
    model = Event
    template_name = 'events/complete_event_list.html'
    context_object_name = 'events'

    def get_queryset(self):
        return Event.objects.filter(status='completed')


# View to create user marks
class CreateUserMark(LoginRequiredMixin, CreateView):
    login_url = 'login'
    model = UserCoin
    fields = ['user', 'gain_type', 'gain_coin', 'status']
    template_name = 'events/create_user_mark.html'

    def form_valid(self, form):
        form.instance.created_user = self.request.user
        form.instance.updated_user = self.request.user
        return super().form_valid(form)


# View to list user marks
class UserMarkList(LoginRequiredMixin, ListView):
    login_url = 'login'
    model = UserCoin
    template_name = 'events/user_mark_list.html'
    context_object_name = 'usermark'


# View to search event categories
@login_required(login_url='login')
def search_event_category(request):
    if request.method == 'POST':
        data = request.POST['search']
        event_category = EventCategory.objects.filter(name__icontains=data)
        context = {
            'event_category': event_category
        }
        return render(request, 'events/event_category.html', context)
    return render(request, 'events/event_category.html')


# View to search events
@login_required(login_url='login')
def search_event(request):
    if request.method == 'POST':
        data = request.POST['search']
        events = Event.objects.filter(name__icontains(data))
        context = {
            'events': events
        }
        return render(request, 'events/event_list.html', context)
    return render(request, 'events/event_list.html')


# View to display dashboard
@login_required
@user_passes_test(is_admin)
def dashboard(request):
    event_ctg = Event.objects.count()
    events = Event.objects.all()
    event = Event.objects.count()
    user = EventRegistration.objects.registrations_last_week()
    complete_event = Event.objects.filter(status='completed').count()

    context = {
        'event_ctg': event_ctg,
        'event': event,
        'events': events,
        'user': user,
        'complete_event': complete_event,
    }
    return render(request, 'dashboard.html', context)

# View for login page
def login_page(request):
    forms = LoginForm()
    if request.method == 'POST':
        forms = LoginForm(request.POST)
        if forms.is_valid():
            username = forms.cleaned_data['username']
            password = forms.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect('e_dashboard')
    context = {
        'form': forms
    }
    return render(request, 'login.html', context)

# View for logout page
def logut_page(request):
    logout(request)
    return redirect('login')
