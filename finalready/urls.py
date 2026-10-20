from django.contrib import admin
from django.urls import include, path
from study import views
urlpatterns = [path('admin/', admin.site.urls), path('accounts/', include('django.contrib.auth.urls')),
               path('accounts/signup/', views.signup, name='signup'), path('', include('study.urls'))]
