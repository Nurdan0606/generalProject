from django.urls import path
from . import views
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('courses/new/', views.course_form, name='course_create'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/<int:pk>/edit/', views.course_form, name='course_edit'),
    path('courses/<int:pk>/upload/', views.upload, name='upload'),
    path('lectures/<int:pk>/generate/', views.generate, name='generate'),
    path('lectures/<int:pk>/open/', views.lecture_open, name='lecture_open'),
    path('lectures/<int:pk>/delete/', views.lecture_delete, name='lecture_delete'),
    path('lectures/<int:pk>/summary/', views.lecture_summary, name='lecture_summary'),
    path('lectures/<int:pk>/summary/generate/', views.summary_generate, name='summary_generate'),
    path('courses/<int:pk>/start/<str:kind>/', views.start, name='start'),
    path('sessions/<int:pk>/', views.quiz, name='quiz'),
    path('demo/', views.demo, name='demo'),
]
