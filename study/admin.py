from django.contrib import admin
from .models import Course, Lecture, Topic, Question, StudySession, SessionItem
admin.site.register([Course, Lecture, Topic, Question, StudySession, SessionItem])
admin.site.site_header = 'FinalReady administration'
