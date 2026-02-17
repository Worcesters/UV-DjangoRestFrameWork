from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.index, name='index'),  # Racine de l'app (la page custom)
    path('api/hello/', views.api_hello, name='api_hello'), # L'URL que HTMX appelle
    path('profile/', views.profile_view, name='profile'), # URL pour le profil
    path('list-users/', views.user_list_partial, name='user_list'), # <-- LE NOM DOIT ETRE ICI
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('docs/add/', views.document_create, name='document_create'),
    path('docs/<slug:slug>/', views.document_detail, name='document_detail'),
]