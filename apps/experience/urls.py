from django.urls import path
from . import views

app_name = 'experience'

urlpatterns = [
    path('explore/', views.game_world_view, name='explore'),
]