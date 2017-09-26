# Description: This is the form where a user can submit feedback on the site.

from Meowseum.models import Feedback, validation_specifications_for_Feedback, hosting_limits_for_Feedback
from Meowseum.file_handling.file_validation import get_validated_metadata
from Meowseum.file_handling.stage2_processing import process_to_meet_hosting_limits
from Meowseum.forms import FeedbackForm
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from Meowseum.common_view_functions import increment_hit_count

def page(request):
    template_variables = {}
    if request.POST:
        form = FeedbackForm(request.POST, request.FILES)
        metadata, form = get_validated_metadata('screenshot', form, request.FILES, validation_specifications_for_Feedback)
        if form.is_valid():
            new_feedback = form.save(commit=False)
            if request.user.is_authenticated():
                new_feedback.author = request.user
            new_feedback.save()
            if new_feedback.screenshot != None:
                new_feedback.screenshot, metadata = process_to_meet_hosting_limits(new_feedback.screenshot, metadata, hosting_limits_for_Feedback)
                new_feedback.save()
            return HttpResponseRedirect(reverse('index'))
        else:
            template_variables['form'] = form
            return render(request, 'en/public/feedback.html', template_variables)
    else:
        increment_hit_count(request, "feedback")
        template_variables['form'] = FeedbackForm()
        return render(request, 'en/public/feedback.html', template_variables)
