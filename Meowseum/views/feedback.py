# Description: This is the form where a user can submit feedback on the site.

from Meowseum.models import Feedback, validation_specifications_for_Feedback, hosting_limits_for_Feedback
from Meowseum.file_handling.file_validation import get_validated_metadata
from Meowseum.file_handling.stage2_processing import process_to_meet_hosting_limits
from Meowseum.forms import FeedbackForm
from django.shortcuts import render
from Meowseum.common_view_functions import redirect, increment_hit_count

def page(request):
    form = FeedbackForm(request.POST or None, request.FILES or None)
    metadata, form = get_validated_metadata('screenshot', form, request.FILES, validation_specifications_for_Feedback)
    if form.is_valid():
        new_feedback = form.save(commit=False)
        if request.user.is_authenticated:
            new_feedback.author = request.user
        new_feedback.save()
        if new_feedback.screenshot != None:
            new_feedback.screenshot, metadata = process_to_meet_hosting_limits(new_feedback.screenshot, metadata, hosting_limits_for_Feedback)
            new_feedback.save()
        return redirect('index')
    else:
        if request.method == 'GET':
            increment_hit_count(request, "feedback")
        return render(request, 'en/public/feedback.html', {'form': form})
