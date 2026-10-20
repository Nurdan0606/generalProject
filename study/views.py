from io import BytesIO
from pathlib import Path
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.db.models import Avg
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError
from pydantic import ValidationError
from .forms import CourseForm, LectureForm
from .models import Course, Lecture, SessionItem, StudySession, Topic
from .services import course_stats, generate_questions, generate_summary, start_session, streak, submit_session

def signup(request):
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.save())
        return redirect('dashboard')
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def dashboard(request):
    courses = [{'course': c, **course_stats(c)} for c in request.user.courses.all()]
    answered = SessionItem.objects.filter(session__course__owner=request.user, session__completed_at__isnull=False)
    total = answered.count()
    return render(request, 'study/dashboard.html', {'courses': courses, 'streak': streak(request.user),
        'accuracy': round(answered.filter(is_correct=True).count() * 100 / total) if total else 0,
        'completed': StudySession.objects.filter(course__owner=request.user, completed_at__isnull=False).count(),
        'history': StudySession.objects.filter(course__owner=request.user, completed_at__isnull=False).select_related('course').order_by('-completed_at')[:5]})

@login_required
def course_form(request, pk=None):
    course = get_object_or_404(Course, pk=pk, owner=request.user) if pk else None
    form = CourseForm(request.POST or None, instance=course)
    if request.method == 'POST' and form.is_valid():
        course = form.save(commit=False)
        course.owner = request.user
        course.save()
        return redirect('course_detail', pk=course.pk)
    return render(request, 'study/form.html', {'form': form, 'title': 'Edit course' if pk else 'Create your course',
        'subtitle': 'Set your final date. Make a little progress every day.', 'button': 'Save course'})

@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk, owner=request.user)
    return render(request, 'study/course.html', {'course': course, 'stats': course_stats(course),
        'topics': course.topics.annotate(mastery=Avg('questions__mastery')).order_by('mastery'),
        'lectures': course.lectures.order_by('-created_at'), 'ai_enabled': bool(settings.OPENAI_API_KEY)})

@login_required
def upload(request, pk):
    course = get_object_or_404(Course, pk=pk, owner=request.user)
    form = LectureForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        lecture = Lecture.objects.create(course=course, title=form.cleaned_data['title'],
            original_name=form.cleaned_data['file'].name, file=form.cleaned_data['file'], text=form.extracted_text)
        if create_summary(request, lecture):
            messages.success(request, 'Lecture uploaded. Your AI summary is ready.')
        else:
            messages.info(request, 'Lecture saved. Open AI summary to retry generation.')
        return redirect('course_detail', pk=pk)
    return render(request, 'study/form.html', {'form': form, 'title': 'Add a lecture',
        'subtitle': course.name + ' - Upload your study material.', 'button': 'Upload lecture', 'upload': True})

def create_summary(request, lecture):
    try:
        generate_summary(lecture)
        return True
    except RateLimitError:
        error = 'OpenAI quota or rate limit reached. Check API billing and usage limits.'
    except APITimeoutError:
        error = 'OpenAI summary generation timed out. Please retry.'
    except APIConnectionError:
        error = 'Could not reach OpenAI. Check your internet connection and retry.'
    except APIStatusError:
        error = 'OpenAI summary generation failed. Check API key, billing and model access, then retry.'
    except ValidationError:
        error = 'OpenAI returned an invalid summary. Please retry.'
    except ValueError as exc:
        error = str(exc)
    messages.error(request, error)
    return False

@login_required
def lecture_open(request, pk):
    lecture = get_object_or_404(Lecture, pk=pk, course__owner=request.user)
    if lecture.file:
        try:
            response = FileResponse(lecture.file.open('rb'),
                as_attachment=True, filename=lecture.original_name)
        except FileNotFoundError:
            raise Http404('Lecture file is missing.') from None
    else:
        # Original files from legacy uploads were never retained. Serve saved text directly.
        response = FileResponse(BytesIO(lecture.text.encode('utf-8')),
            content_type='text/plain; charset=utf-8',
            as_attachment=True,
            filename=Path(lecture.original_name).stem + '.txt')
    response['Cache-Control'] = 'private, no-store'
    return response

@login_required
@require_POST
def lecture_delete(request, pk):
    with transaction.atomic():
        lecture = get_object_or_404(Lecture.objects.select_for_update(), pk=pk, course__owner=request.user)
        course_id = lecture.course_id
        topic_ids = list(lecture.questions.values_list('topic_id', flat=True))
        storage, filename = lecture.file.storage, lecture.file.name
        lecture.delete()
        Topic.objects.filter(pk__in=topic_ids, questions__isnull=True).delete()
        if filename:
            transaction.on_commit(lambda: storage.delete(filename))
    messages.success(request, 'Lecture deleted.')
    return redirect('course_detail', pk=course_id)

@login_required
def lecture_summary(request, pk):
    lecture = get_object_or_404(Lecture, pk=pk, course__owner=request.user)
    summary = lecture.summary if lecture.summary.get('language') == 'en' else None
    return render(request, 'study/summary.html', {'lecture': lecture, 'summary': summary})

@login_required
@require_POST
def summary_generate(request, pk):
    lecture = get_object_or_404(Lecture, pk=pk, course__owner=request.user)
    create_summary(request, lecture)
    return redirect('lecture_summary', pk=pk)

@login_required
@require_POST
def generate(request, pk):
    lecture = get_object_or_404(Lecture, pk=pk, course__owner=request.user)
    try:
        count = generate_questions(lecture)
        messages.success(request, f'{count} questions added.' if count else 'This lecture already has a question bank.')
    except ValidationError:
        messages.error(request, 'Invalid generated content. Please retry.')
    except ValueError as exc:
        messages.error(request, str(exc))
    except RateLimitError:
        messages.error(request, 'OpenAI quota or rate limit reached. Check API billing and usage limits, then retry.')
    except APITimeoutError:
        messages.error(request, 'OpenAI took too long to generate the question bank. Please retry.')
    except APIConnectionError:
        messages.error(request, 'Could not reach OpenAI. Check your internet connection and retry.')
    except APIStatusError as exc:
        if exc.status_code >= 500:
            messages.error(request, 'OpenAI is temporarily unavailable. The SDK retried automatically; please try again shortly.')
        else:
            messages.error(request, 'OpenAI generation failed. Check your API key, billing, and model access, then retry.')
    return redirect('course_detail', pk=lecture.course_id)

@login_required
@require_POST
def start(request, pk, kind):
    course = get_object_or_404(Course, pk=pk, owner=request.user)
    if kind not in {'daily', 'weekly'}:
        raise Http404
    try:
        session = start_session(course, kind)
    except ValueError as exc:
        messages.info(request, str(exc))
        return redirect('course_detail', pk=pk)
    return redirect('quiz', pk=session.pk)

@login_required
def quiz(request, pk):
    session = get_object_or_404(StudySession.objects.select_related('course'), pk=pk, course__owner=request.user)
    if request.method == 'POST':
        try:
            submit_session(session, request.POST)
            return redirect('quiz', pk=pk)
        except ValueError as exc:
            messages.error(request, str(exc))
    items = list(session.items.select_related('question__topic'))
    for item in items:
        item.options = [{'index': i, 'text': text, 'chosen': i == item.selected_index,
                         'correct': i == item.question.correct_index} for i, text in enumerate(item.question.choices)]
    return render(request, 'study/quiz.html', {'session': session, 'items': items})

@login_required
@require_POST
def demo(request):
    from .demo import create_demo
    course = create_demo(request.user)
    return redirect('course_detail', pk=course.pk)
