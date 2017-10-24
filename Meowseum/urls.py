from django.conf.urls import url, include
from django.contrib import admin
from .views import *
from django.conf import settings
from django.conf.urls.static import static
# These lines pre-emptively import the built-in classes and functions for CBVs.
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.contrib.auth.decorators import login_required
admin.autodiscover()

urlpatterns = [
    url(r'^$', gallery.front_page, name="index"),
    url(r'^index/$', gallery.front_page),
    url(r'^site_statistics', site_statistics.page, name="site_statistics"),
    url(r'^login/$', login.page, name="login"),
    url(r'^logout/$', logout.page, name="logout"),
    url(r'^signup/$', signup.page, name="signup"),
    url(r'^tou/$', tou.page, name="tou"),
    url(r'^privacy/$', privacy.page, name="privacy"),
    url(r'^about_us/$', about_us.page, name="about_us"),
    url(r'^advanced_search/$', advanced_search.page, name="advanced_search"),
    url(r'^from_device/$', from_device.page, name="from_device"),
    url(r'^upload_page1/$', upload_page1.page, name="upload_page1"),
    url(r'^user_contact_information/$', user_contact_information.page, name="user_contact_information"),
    url(r'^shelter_contact_information/$', shelter_contact_information.page, name="shelter_contact_information"),
    url(r'^adoption_upload/$', adoption_upload.page, name="adoption_upload"),
    url(r'^lost_upload/$', lost_upload.page, name="lost_upload"),
    url(r'^found_upload/$', found_upload.page, name="found_upload"),
    url(r'^slide/(?P<relative_url>.+)/$', slide_page.page, name="slide_page"),
    url(r'^slide/(?P<relative_url>.+)/edit_upload$', edit_upload.page, name="edit_upload"),
    url(r'^slide/(?P<relative_url>.+)/delete_upload$', delete_upload.page, name="delete_upload"),
    url(r'^slide/(?P<relative_url>.+)/like$', like.page, name="like"),
    url(r'^slide/(?P<relative_url>.+)/add_tag$', add_tag.page, name="add_tag"),
    url(r'^slide/(?P<relative_url>.+)/add_comment$', add_comment.page, name="add_comment"),
    url(r'^delete_comment/(?P<comment_id>.+)/$', delete_comment.page, name="delete_comment"),
    url(r'^user/(?P<username>.+)/follow$', follow.page, name="follow"),
    url(r'^user/(?P<username>.+)/mute$', mute.page, name="mute"),
    url(r'^user/(?P<username>.+)/ban$', ban.page, name="ban"),
    url(r'^feedback/$', feedback.page, name="feedback"),
    url(r'^report_abuse/$', report_abuse.page, name="report_abuse"),
    url(r'^user_profile/$', user_profile.page, name="user_profile"),
    url(r'^user/(?P<username>.+)/gallery/$', gallery.uploads, name="gallery"),
    url(r'^your_gallery/$', gallery.your_uploads, name="your_gallery"),
    url(r'^user/(?P<username>.+)/likes/$', gallery.likes, name="likes"),
    url(r'^your_likes/$', gallery.your_likes, name="your_likes"),
    url(r'^user/(?P<username>.+)/comments/$', user_comments.page, name="user_comments"),
    url(r'^followed_users/$', gallery.from_followed_users, name="followed_users"),
    url(r'^your_comments/$', user_comments.your_comments, name="your_comments"),
    url(r'^random_upload/$', random_upload.page, name="random_slide"),
    url(r'^new_submissions/$', gallery.new_submissions, name="new_submissions"),
    url(r'^most_popular/$', gallery.most_popular, name="most_popular"),
    url(r'^tag/(?P<tag_name>.+)/$', gallery.tag_gallery, name="tag_gallery"),
    url(r'^tag/(?P<tag_name>.+)/subscribe$', subscribe.page, name="subscribe"),
    url(r'^subscribed_tags/$', gallery.subscribed_tags, name="subscribed_tags"),
    url(r'^search/$', search.page, name="search"),
    url(r'^header_search/$', search.header_search, name="header_search"),
    url(r'^adoption_search/$', adoption_search.page, name="adoption_search"),
    url(r'^lost_search/$', lost_search.page, name="lost_search"),
    url(r'^found_search/$', found_search.page, name="found_search"),
    url(r'^shelter_search/$', shelter_search.page, name="shelter_search"),
    url(r'^toggle_mobile_play_button/$', toggle_mobile_play_button.page, name="toggle_mobile_play_button"),
    url(r'^toggle_night_mode/$', toggle_night_mode.page, name="toggle_night_mode"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
