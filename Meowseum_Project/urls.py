"""Project_directory URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView
from django.views.generic.list import ListView
from Meowseum.models import Upload
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.conf.urls.static import static
admin.autodiscover()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^admin', include(admin.site.urls)),
    url(r'^site_statistics', 'Meowseum.views.site_statistics.page', name="site_statistics"),
    url(r'^$', 'Meowseum.views.gallery.front_page', name="index"),
    url(r'^index/$', 'Meowseum.views.gallery.front_page'),
    url(r'^login/$', 'Meowseum.views.login.page', name="login"),
    url(r'^logout/$', 'Meowseum.views.logout.page', name="logout"),
    url(r'^signup/$', 'Meowseum.views.signup.page', name="signup"),
    url(r'^tou/$', 'Meowseum.views.tou.page', name="tou"),
    url(r'^privacy/$', 'Meowseum.views.privacy.page', name="privacy"),
    url(r'^about_us/$', 'Meowseum.views.about_us.page', name="about_us"),
    url(r'^advanced_search/$', 'Meowseum.views.advanced_search.page', name="advanced_search"),
    url(r'^from_device/$', 'Meowseum.views.forms.from_device.page', name="from_device"),
    url(r'^upload_page1/$', 'Meowseum.views.upload_page1.page', name="upload_page1"),
    url(r'^user_contact_information/$', 'Meowseum.views.user_contact_information.page', name="user_contact_information"),
    url(r'^shelter_contact_information/$', 'Meowseum.views.shelter_contact_information.page', name="shelter_contact_information"),
    url(r'^adoption_upload/$', 'Meowseum.views.adoption_upload.page', name="adoption_upload"),
    url(r'^lost_upload/$', 'Meowseum.views.lost_upload.page', name="lost_upload"),
    url(r'^found_upload/$', 'Meowseum.views.found_upload.page', name="found_upload"),
    url(r'^slide/(?P<relative_url>.+)/$', 'Meowseum.views.slide_page.page', name="slide_page"),
    url(r'^slide/(?P<relative_url>.+)/like$', 'Meowseum.views.like.page', name="like"),
    url(r'^slide/(?P<relative_url>.+)/delete_upload$', 'Meowseum.views.delete_upload.page', name="delete_upload"),
    url(r'^slide/(?P<relative_url>.+)/add_tag$', 'Meowseum.views.add_tag.page', name="add_tag"),
    url(r'^user/(?P<username>.+)/follow$', 'Meowseum.views.follow.page', name="follow"),
    url(r'^user/(?P<username>.+)/mute$', 'Meowseum.views.mute.page', name="mute"),
    url(r'^user/(?P<username>.+)/ban$', 'Meowseum.views.ban.page', name="ban"),
    url(r'^feedback/$', 'Meowseum.views.feedback.page', name="feedback"),
    url(r'^report_abuse/$', 'Meowseum.views.report_abuse.page', name="report_abuse"),
    url(r'^user_profile/$', 'Meowseum.views.user_profile.page', name="user_profile"),
    url(r'^user/(?P<username>.+)/gallery/$', 'Meowseum.views.gallery.uploads', name="gallery"),
    url(r'^your_gallery/$', 'Meowseum.views.gallery.your_uploads', name="your_gallery"),
    url(r'^user/(?P<username>.+)/likes/$', 'Meowseum.views.gallery.likes', name="likes"),
    url(r'^your_likes/$', 'Meowseum.views.gallery.your_likes', name="your_likes"),
    url(r'^user/(?P<username>.+)/comments/$', 'Meowseum.views.user_comments.page', name="user_comments"),
    url(r'^followed_users/$', 'Meowseum.views.gallery.from_followed_users', name="followed_users"),
    url(r'^your_comments/$', 'Meowseum.views.user_comments.your_comments', name="your_comments"),
    url(r'^random_upload/$', 'Meowseum.views.random_upload.page', name="random_slide"),
    url(r'^new_submissions/$', 'Meowseum.views.gallery.new_submissions', name="new_submissions"),
    url(r'^most_popular/$', 'Meowseum.views.gallery.most_popular', name="most_popular"),
    url(r'^tag/(?P<tag_name>.+)/$', 'Meowseum.views.gallery.tag_gallery', name="tag_gallery"),
    url(r'^tag/(?P<tag_name>.+)/subscribe$', 'Meowseum.views.subscribe.page', name="subscribe"),
    url(r'^subscribed_tags/$', 'Meowseum.views.gallery.subscribed_tags', name="subscribed_tags"),
    url(r'^search/$', 'Meowseum.views.search.page', name="search"),
    url(r'^header_search/$', 'Meowseum.views.search.header_search', name="header_search"),
    url(r'^adoption_search/$', 'Meowseum.views.adoption_search.page', name="adoption_search"),
    url(r'^lost_search/$', 'Meowseum.views.lost_search.page', name="lost_search"),
    url(r'^found_search/$', 'Meowseum.views.found_search.page', name="found_search"),
    url(r'^shelter_search/$', 'Meowseum.views.shelter_search.page', name="shelter_search"),
    url(r'^toggle_night_mode/$', 'Meowseum.views.toggle_night_mode.page', name="toggle_night_mode"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
