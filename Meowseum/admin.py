from django.contrib import admin
from Meowseum.models import Page, ExceptionRecord, TemporaryUpload, Upload, Metadata, Tag, Like, Comment, UserProfile, AbuseReport, Feedback, UserContact, Shelter, Adoption, Lost, Found

# Register your models here.
admin.site.register(Page)
admin.site.register(ExceptionRecord)
admin.site.register(TemporaryUpload)
admin.site.register(Upload)
admin.site.register(Metadata)
admin.site.register(Tag)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(UserProfile)
admin.site.register(AbuseReport)
admin.site.register(Feedback)
admin.site.register(UserContact)
admin.site.register(Shelter)
admin.site.register(Adoption)
admin.site.register(Lost)
admin.site.register(Found)
