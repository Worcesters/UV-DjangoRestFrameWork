from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.index, name='index'),
    path('profil-public/', views.public_profile_view, name='public_profile'),
    path('documents/', views.documents_page, name='documents'),
    path('api/hello/', views.api_hello, name='api_hello'),
    path('profile/', views.profile_view, name='profile'),
    path('list-users/', views.user_list_partial, name='user_list'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('docs/add/', views.document_create, name='document_create'),
    path('docs/<slug:slug>/', views.document_detail, name='document_detail'),
]