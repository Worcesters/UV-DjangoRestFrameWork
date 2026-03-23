from django.views.generic import ListView

from .models import Experience


class GameWorldView(ListView):
    """Scène 3D : liste des expériences pour le HUD / vignettes."""

    model = Experience
    template_name = "experience/game_world.html"
    context_object_name = "experiences"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_tab"] = "game"
        return context
