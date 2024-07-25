# userPortal/middleware.py
from django.utils import timezone
from django.conf import settings
from django.shortcuts import redirect
from django.utils.dateparse import parse_datetime

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_time = timezone.now()
            last_activity = request.session.get('last_activity')
            if last_activity:
                last_activity = parse_datetime(last_activity)
                if last_activity and timezone.is_naive(last_activity):
                    last_activity = timezone.make_aware(last_activity, timezone.get_default_timezone())
                elapsed_time = (current_time - last_activity).total_seconds()
                if elapsed_time > settings.SESSION_COOKIE_AGE:
                    from django.contrib.auth import logout
                    logout(request)
                    return redirect('login_as_customer')

            request.session['last_activity'] = current_time.isoformat()

        response = self.get_response(request)
        return response
