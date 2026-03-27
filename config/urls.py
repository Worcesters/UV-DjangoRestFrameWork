"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import path, include

from apps.users.views import catch_all_404, page_not_found

handler404 = page_not_found

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.users.urls')), # On branche l'app users sur la racine
    path('world/', include('apps.experience.urls')), # On branche le nouveau module world sur /world/
    path('uml/', include('apps.code_converter_uml.urls')),
    path('codegenerator/', include('apps.codegenerator.urls')),
    path('pipeline-generator/', include('apps.pipeline_generator.urls')),
    path('code-to-bpmn/', include('apps.code_to_bpmn.urls')),
    path('contact/', include('apps.contact.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/404/", lambda request: page_not_found(request, None), name="debug_404_preview"),
        # Dernière route : toute URL invalide affiche la 404 (en prod, c’est handler404 ci-dessus).
        path("<path:catchall>", catch_all_404, name="catchall_404"),
    ]