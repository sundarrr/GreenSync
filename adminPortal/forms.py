from django import forms
from betterforms.multiform import MultiModelForm

# Importing necessary models for our forms
from .models import Event, EventImage, EventAgenda

# Defining the form for Event model
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['category', 'name', 'uid', 'description', 'scheduled_status', 'venue', 'start_date', 'end_date', 'location', 'maximum_attende', 'status']
        # Setting the fields for the Event form. You can uncomment the next line if you need to include 'job_category' and 'points'.
        # fields = ['category', 'name', 'uid', 'description', 'job_category', 'scheduled_status', 'venue', 'start_date',
                  # 'end_date', 'location', 'points', 'maximum_attende', 'status']
        # Customizing widgets for the start_date and end_date fields to use date input
        widgets = {
            'start_date': forms.TextInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.TextInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

# Defining the form for EventImage model
class EventImageForm(forms.ModelForm):
    class Meta:
        model = EventImage
        fields = ['image']

# Defining the form for EventAgenda model
class EventAgendaForm(forms.ModelForm):
    class Meta:
        model = EventAgenda
        fields = ['session_name', 'speaker_name', 'start_time', 'end_time', 'venue_name']
        # Customizing widgets for the start_time and end_time fields to use time input
        widgets = {
            'start_time': forms.TextInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TextInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

# MultiModelForm to handle multiple forms (EventForm, EventImageForm, EventAgendaForm) together
class EventCreateMultiForm(MultiModelForm):
    form_classes = {
        'event': EventForm,
        'event_image': EventImageForm,
        'event_agenda': EventAgendaForm,
    }

# Defining a simple login form with username and password fields
class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'type': 'text',
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'type': 'password',
        'placeholder': 'Password'
    }))
