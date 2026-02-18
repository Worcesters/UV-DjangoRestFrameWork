from django.shortcuts import render
from .models import Experience

def game_world_view(request):
    experiences = Experience.objects.all()
    return render(request, "experience/game_world.html", {
        "experiences": experiences,
        "active_tab": "game"
    })