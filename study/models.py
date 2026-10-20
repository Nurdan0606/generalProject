from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

class Course(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=120)
    exam_date = models.DateField()
    daily_minutes = models.PositiveSmallIntegerField(default=10, validators=[MinValueValidator(1), MaxValueValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['exam_date', 'name']

    def __str__(self):
        return self.name

    @property
    def days_left(self):
        return max(0, (self.exam_date - timezone.localdate()).days)

class Lecture(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lectures')
    title = models.CharField(max_length=200)
    original_name = models.CharField(max_length=255)
    text = models.TextField()
    file = models.FileField(upload_to='lectures/%Y/%m/', blank=True)
    summary = models.JSONField(default=dict, blank=True)
    generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Topic(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=160)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['course', 'name'], name='unique_course_topic')]

class Question(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='questions')
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='questions')
    prompt = models.TextField()
    choices = models.JSONField()
    correct_index = models.PositiveSmallIntegerField(validators=[MaxValueValidator(3)])
    explanation = models.TextField()
    mastery = models.FloatField(default=0)
    attempts = models.PositiveIntegerField(default=0)
    due_date = models.DateField(default=timezone.localdate)

class StudySession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sessions')
    kind = models.CharField(max_length=10, choices=[('daily', 'Daily quiz'), ('weekly', 'Weekly review')])
    period_date = models.DateField()
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['course', 'kind', 'period_date'], name='unique_study_period')]

    @property
    def score(self):
        total = self.items.count()
        return round(100 * self.items.filter(is_correct=True).count() / total) if total else 0

class SessionItem(models.Model):
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name='items')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    selected_index = models.PositiveSmallIntegerField(null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ['position']
        constraints = [models.UniqueConstraint(fields=['session', 'question'], name='unique_session_question')]
