# Description: Django middleware is a framework of programs for processing requests, template responses, and exception pages.
# This file contains custom middleware for how the program should process requests when the user has been banned.
# Currently, it only logs out the user when the user is banned, but in the future this would also be the place to filter out users by IP addresses.

from django.contrib.auth import logout

class LogoutBannedUserMiddleware(object):
    # When a user's account is disabled, Django will force the user to log out as soon as the user visits another page.
    def process_request(self, request):
        if request.user.is_authenticated and not request.user.is_active:
           logout(request)
