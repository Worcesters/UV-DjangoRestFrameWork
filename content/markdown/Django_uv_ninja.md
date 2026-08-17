# Django 2026

> **Stack :** Python 3.12+ | Django 5.x / 6.x | Django Ninja | Pydantic v2 | uv | Astro | HTMX 2.x | PostgreSQL 16 | Redis | Celery | Docker Compose
> **Structure :** monorepo `backend/` + `frontend/`
> **Règle d’or :** la logique métier vit dans **Services / Selectors**, jamais dans les routers Ninja, les templates HTMX, ni Astro.

Ce guide est un **tuto plug-and-play** : chaque section est copiable. À la fin, tu as une API Ninja, un back-office HTMX, un site produit Astro, et un `docker compose` qui démarre le tout.

---

## Table des matières {#toc}

1. [Les trois piliers](#combo-0)
2. [Arborescence cible](#combo-1)
3. [Prérequis](#combo-2)
4. [Jour 0 — scaffold backend (uv + Django + Ninja)](#combo-3)
5. [Settings `base` / `dev` / `prod`](#combo-4)
6. [Healthcheck](#combo-5)
7. [Service Layer + Ninja — `catalog`](#combo-6)
8. [Deuxième app — `orders`](#combo-7)
9. [Assembler les routers](#combo-8)
10. [Back-office HTMX (staff)](#combo-9)
11. [UI produit Astro](#combo-10)
12. [Celery + Redis](#combo-11)
13. [Docker Compose (dev)](#combo-12)
14. [Nginx prod (schéma)](#combo-13)
15. [Auth, CORS, secrets](#combo-14)
16. [Tests](#combo-15)
17. [Ninja vs DRF](#combo-16)
18. [Checklist plug-and-play](#combo-17)
19. [Résumé](#combo-18)

---

## 1. Les trois piliers {#combo-0}

| Pilier | Techno | Rôle |
| :--- | :--- | :--- |
| **API / métier** | **Django Ninja** | JSON, schemas Pydantic, orchestration → services / selectors |
| **UI produit** | **Astro** (`frontend/`) | Site public, SEO, islands |
| **UI interne** | **HTMX** (templates Django) | Admin, back-office, CRUD staff |

Les trois coexistent dans **le même monorepo**. Ce n’est pas Astro *ou* HTMX : c’est Astro *et* HTMX, avec Ninja au centre.

| Surface | Où ça vit | Consomme |
| :--- | :--- | :--- |
| Pages publiques / catalogue | `frontend/` (Astro) | `GET /api/...` |
| CRUD staff / outils internes | `backend/templates/` + CBV | **les mêmes** services / selectors |
| Clients mobiles / partenaires | `/api/` Ninja | schemas Pydantic |

**Interdit :** Next.js, Tailwind / utility-first, `pip` / `poetry` / `pipenv`, logique métier dans Astro ou dans les vues HTMX.

---

## 2. Arborescence cible {#combo-1}

```
boutique/
├── backend/                      # Django (API Ninja + HTMX)
│   ├── manage.py
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── config/
│   │   ├── api.py                # NinjaAPI racine
│   │   ├── celery.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   └── settings/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── dev.py
│   │       ├── qua.py
│   │       └── prod.py
│   ├── apps/
│   │   ├── catalog/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── selectors.py
│   │   │   ├── services.py
│   │   │   ├── api.py
│   │   │   ├── views.py          # CBV HTMX uniquement
│   │   │   ├── forms.py
│   │   │   ├── urls.py
│   │   │   └── tasks.py
│   │   └── orders/
│   │       └── … (même patron)
│   ├── templates/                # UI interne HTMX
│   │   ├── base.html
│   │   └── catalog/partials/
│   └── static/scss|css|js/
├── frontend/                     # Astro — UI produit
│   ├── src/pages/
│   ├── src/layouts/
│   ├── src/components/
│   ├── src/styles/
│   ├── src/lib/api/
│   ├── astro.config.mjs
│   ├── package.json
│   └── Dockerfile
├── docker-compose.dev.yml
├── docker-compose.yml            # prod-like (optionnel jour 0)
├── .env.example
└── nginx/nginx.conf              # prod
```

| Zone | Responsabilité |
| :--- | :--- |
| `config/api.py` | Instance `NinjaAPI`, OpenAPI, handlers d’erreur |
| `apps/*/api.py` | Endpoints : schema → service/selector → schema |
| `apps/*/schemas.py` | Contrats JSON (Pydantic) — **pas** de métier |
| `apps/*/services.py` | Écriture, invariants, transactions |
| `apps/*/selectors.py` | Lecture optimisée |
| `apps/*/views.py` | **CBV uniquement** (back-office HTMX) |
| `frontend/` | Présentation produit — **pas** de métier |

---

## 3. Prérequis {#combo-2}

| Outil | Version mini | Vérification |
| :--- | :--- | :--- |
| **uv** | dernier | `uv --version` |
| **Python** | 3.12+ (installé par uv) | `uv python list` |
| **Node.js** | 22 | `node -v` |
| **Docker Desktop** | Compose v2 | `docker compose version` |

### Installer uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Puis : `uv --version`. Mise à jour : `uv self update`.

Doc officielle : [Installation uv](https://docs.astral.sh/uv/getting-started/installation/).

---

## 4. Jour 0 — scaffold backend (uv + Django + Ninja) {#combo-3}

Depuis un dossier vide (exemple : `boutique/`) :

```bash
mkdir boutique && cd boutique
mkdir backend frontend
cd backend
```

```bash
uv init --python 3.12
# uv crée parfois un main.py de démo : tu peux le supprimer.
```

Dépendances runtime :

```bash
uv add "django>=5.2" django-ninja django-environ dj-database-url \
  gunicorn whitenoise "psycopg[binary]" celery redis django-cors-headers django-htmx
```

Dépendances de dev :

```bash
uv add --dev pytest pytest-django ruff
```

Créer le projet Django **dans** `backend/` (le module s’appelle `config`) :

```bash
uv run django-admin startproject config .
```

Créer le paquet d’apps et deux apps métier :

```bash
mkdir -p apps
uv run python manage.py startapp catalog apps/catalog
uv run python manage.py startapp orders apps/orders
```

Dans `apps/catalog/apps.py` (et idem `orders`) :

```python
name = "apps.catalog"
```

Vérifier Ninja :

```bash
uv run python -c "import ninja, django; print('ninja', ninja.__version__, 'django', django.get_version())"
```

`INSTALLED_APPS` : **pas besoin** d’une app `ninja` — c’est une librairie, pas une app Django. En revanche, ajoute `django_htmx` et tes apps.

---

## 5. Settings `base` / `dev` / `prod` {#combo-4}

Découpe obligatoire : `config/settings/base.py` (commun) + overrides par environnement.

### `config/settings/__init__.py`

```python
from .dev import *  # noqa: F403
```

En Docker / prod, tu overrides via `DJANGO_SETTINGS_MODULE=config.settings.prod`.

### Extraire de `config/settings.py` vers `config/settings/base.py`

Points à coller (le reste du `startproject` reste valide) :

```python
from pathlib import Path

import dj_database_url
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-only-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "django_htmx",
    "apps.catalog",
    "apps.orders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": dj_database_url.parse(
        env("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
    )
}

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://127.0.0.1:6379/1")
```

### `config/settings/dev.py`

```python
from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "backend"]
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4321",
    "http://127.0.0.1:4321",
]
```

SQLite est **toléré en local uniquement**. Dès que tu lances Compose, `DATABASE_URL` pointe vers PostgreSQL 16.

---

## 6. Healthcheck {#combo-5}

Les conteneurs (et le load balancer) pingent `/health/`. Vue **CBV**, sans métier.

### `apps/catalog/views.py` (extrait) ou petite app `core`

```python
from django.http import HttpResponse
from django.views import View


class HealthView(View):
    """Sonde liveness / readiness (infra)."""

    def get(self, request):
        return HttpResponse("ok", content_type="text/plain")
```

### `config/urls.py` (amorce)

```python
from django.contrib import admin
from django.urls import include, path

from apps.catalog.views import HealthView
from config.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", HealthView.as_view(), name="health"),
    path("backoffice/", include("apps.catalog.urls")),
    path("api/", api.urls),
]
```

Test manuel :

```bash
uv run python manage.py migrate
uv run python manage.py runserver
# → http://127.0.0.1:8000/health/  doit afficher : ok
```

---

## 7. Service Layer + Ninja — `catalog` {#combo-6}

Patron à répliquer dans **chaque** app exposant des données :

```text
apps/catalog/
├── models.py       # schéma BDD uniquement
├── schemas.py      # ProductIn, ProductOut, ProductListOut
├── selectors.py    # get_product(), list_products()
├── services.py     # create_product()
└── api.py          # Router (orchestration fine)
```

**Interdit dans `api.py` :** `Product.objects.create(...)`, règles métier, boucles d’écriture.

### `apps/catalog/models.py`

```python
from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name
```

### `apps/catalog/schemas.py`

```python
from datetime import datetime
from decimal import Decimal

from ninja import Schema


class ProductIn(Schema):
    name: str
    slug: str
    price: Decimal
    is_active: bool = True


class ProductOut(Schema):
    id: int
    name: str
    slug: str
    price: Decimal
    is_active: bool
    created_at: datetime


class ProductListOut(Schema):
    items: list[ProductOut]
    count: int
```

### `apps/catalog/selectors.py`

```python
from django.db.models import QuerySet

from apps.catalog.models import Product


def list_products(*, active_only: bool = True) -> QuerySet[Product]:
    qs = Product.objects.all().order_by("-created_at")
    if active_only:
        qs = qs.filter(is_active=True)
    return qs


def get_product(*, product_id: int) -> Product:
    return Product.objects.get(pk=product_id)
```

### `apps/catalog/services.py`

```python
from decimal import Decimal

from django.db import transaction

from apps.catalog.models import Product


class ProductAlreadyExistsError(Exception):
    pass


@transaction.atomic
def create_product(
    *,
    name: str,
    slug: str,
    price: Decimal,
    is_active: bool = True,
) -> Product:
    if Product.objects.filter(slug=slug).exists():
        raise ProductAlreadyExistsError(f"Slug déjà utilisé : {slug}")
    return Product.objects.create(
        name=name,
        slug=slug,
        price=price,
        is_active=is_active,
    )
```

### `apps/catalog/api.py`

```python
from ninja import Router
from ninja.errors import HttpError

from apps.catalog import services
from apps.catalog.models import Product
from apps.catalog.schemas import ProductIn, ProductListOut, ProductOut
from apps.catalog.selectors import get_product, list_products

router = Router()


@router.get("/products", response=ProductListOut)
def products_list(request, active_only: bool = True) -> ProductListOut:
    items = list(list_products(active_only=active_only))
    return ProductListOut(
        items=[ProductOut.from_orm(p) for p in items],
        count=len(items),
    )


@router.get("/products/{product_id}", response=ProductOut)
def products_detail(request, product_id: int) -> ProductOut:
    try:
        product = get_product(product_id=product_id)
    except Product.DoesNotExist:
        raise HttpError(404, "Produit introuvable")
    return ProductOut.from_orm(product)


@router.post("/products", response={201: ProductOut})
def products_create(request, payload: ProductIn) -> tuple[int, ProductOut]:
    try:
        product = services.create_product(**payload.model_dump())
    except services.ProductAlreadyExistsError as exc:
        raise HttpError(409, str(exc))
    return 201, ProductOut.from_orm(product)
```

> **Note Pydantic v2 :** selon la version de Ninja, préférer `ProductOut.model_validate(product)` à `from_orm` si déprécié.

Migrer :

```bash
uv run python manage.py makemigrations catalog
uv run python manage.py migrate
```

---

## 8. Deuxième app — `orders` {#combo-7}

`orders` **consomme** `catalog` via les **services / selectors** (jamais via un appel HTTP interne).

### `apps/orders/models.py`

```python
from django.db import models

from apps.catalog.models import Product


class Order(models.Model):
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
```

### `apps/orders/schemas.py`

```python
from datetime import datetime
from decimal import Decimal

from ninja import Schema


class OrderLineIn(Schema):
    product_id: int
    quantity: int


class OrderIn(Schema):
    email: str
    lines: list[OrderLineIn]


class OrderLineOut(Schema):
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal


class OrderOut(Schema):
    id: int
    email: str
    created_at: datetime
    lines: list[OrderLineOut]
    total: Decimal
```

### `apps/orders/services.py`

```python
from decimal import Decimal

from django.db import transaction

from apps.catalog.selectors import get_product
from apps.orders.models import Order, OrderLine


class OrderValidationError(Exception):
    pass


@transaction.atomic
def create_order(*, email: str, lines: list[dict]) -> Order:
    if not lines:
        raise OrderValidationError("La commande doit contenir au moins une ligne.")

    order = Order.objects.create(email=email)

    for line in lines:
        product = get_product(product_id=line["product_id"])
        if line["quantity"] < 1:
            raise OrderValidationError("Quantité invalide.")
        if not product.is_active:
            raise OrderValidationError(f"Produit inactif : {product.slug}")

        OrderLine.objects.create(
            order=order,
            product=product,
            quantity=line["quantity"],
            unit_price=product.price,
        )

    return order
```

### `apps/orders/selectors.py`

```python
from decimal import Decimal

from django.db.models import Prefetch

from apps.orders.models import Order, OrderLine


def get_order(*, order_id: int) -> Order:
    return (
        Order.objects.prefetch_related(
            Prefetch("lines", queryset=OrderLine.objects.select_related("product"))
        ).get(pk=order_id)
    )


def order_total(*, order: Order) -> Decimal:
    return sum(
        (line.unit_price * line.quantity for line in order.lines.all()),
        Decimal("0"),
    )
```

### `apps/orders/api.py`

```python
from ninja import Router
from ninja.errors import HttpError

from apps.orders import services
from apps.orders.models import Order
from apps.orders.schemas import OrderIn, OrderLineOut, OrderOut
from apps.orders.selectors import get_order, order_total

router = Router()


def _serialize_order(order) -> OrderOut:
    lines = [
        OrderLineOut(
            product_id=line.product_id,
            product_name=line.product.name,
            quantity=line.quantity,
            unit_price=line.unit_price,
        )
        for line in order.lines.all()
    ]
    return OrderOut(
        id=order.id,
        email=order.email,
        created_at=order.created_at,
        lines=lines,
        total=order_total(order=order),
    )


@router.post("", response={201: OrderOut})
def orders_create(request, payload: OrderIn) -> tuple[int, OrderOut]:
    try:
        order = services.create_order(
            email=payload.email,
            lines=[line.model_dump() for line in payload.lines],
        )
    except services.OrderValidationError as exc:
        raise HttpError(400, str(exc))

    order = get_order(order_id=order.id)
    return 201, _serialize_order(order)


@router.get("/{order_id}", response=OrderOut)
def orders_detail(request, order_id: int) -> OrderOut:
    try:
        order = get_order(order_id=order_id)
    except Order.DoesNotExist:
        raise HttpError(404, "Commande introuvable")
    return _serialize_order(order)
```

```bash
uv run python manage.py makemigrations orders
uv run python manage.py migrate
```

---

## 9. Assembler les routers {#combo-8}

### `config/api.py`

```python
from ninja import NinjaAPI

from apps.catalog.services import ProductAlreadyExistsError

api = NinjaAPI(
    title="Boutique API",
    version="1.0.0",
    description="API REST type-safe — catalog + orders",
    docs_url="/docs",
    openapi_url="/openapi.json",
)


@api.exception_handler(ProductAlreadyExistsError)
def on_duplicate(request, exc):
    return api.create_response(request, {"detail": str(exc)}, status=409)
```

### Montage dans `config/urls.py`

```python
from config.api import api
from apps.catalog.api import router as catalog_router
from apps.orders.api import router as orders_router

api.add_router("/catalog", catalog_router, tags=["catalog"])
api.add_router("/orders", orders_router, tags=["orders"])
```

URLs finales :

| Méthode | URL | Action |
| :--- | :--- | :--- |
| `GET` | `/health/` | Sonde |
| `GET` | `/api/catalog/products` | Liste produits |
| `POST` | `/api/catalog/products` | Créer un produit |
| `GET` | `/api/catalog/products/{id}` | Détail |
| `POST` | `/api/orders` | Créer une commande |
| `GET` | `/api/docs` | Swagger UI |

Smoke API (après `runserver`) :

```bash
curl http://127.0.0.1:8000/api/catalog/products
curl -X POST http://127.0.0.1:8000/api/catalog/products \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"T-shirt\",\"slug\":\"t-shirt\",\"price\":\"19.99\"}"
```

---

## 10. Back-office HTMX (staff) {#combo-9}

Surface **interne uniquement**. Les CBV appellent **les mêmes** `list_products` / `create_product` que Ninja. Détail HTMX : [Django_uv_htmx.md](/docs/django-uv-htmx/).

### `apps/catalog/urls.py`

```python
from django.urls import path

from apps.catalog.views import ProductCreateView, ProductListView

app_name = "catalog"

urlpatterns = [
    path("products/", ProductListView.as_view(), name="product_list"),
    path("products/new/", ProductCreateView.as_view(), name="product_create"),
]
```

### `apps/catalog/forms.py` (rendu HTML seulement)

```python
from django import forms

from apps.catalog.models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "slug", "price", "is_active")
```

### `apps/catalog/views.py` (CBV)

```python
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from apps.catalog.forms import ProductForm
from apps.catalog.models import Product
from apps.catalog.selectors import list_products
from apps.catalog.services import create_product


class ProductListView(ListView):
    """Liste staff des produits.

    MRO:
    1. ListView.get → get_queryset via selector
    2. request.htmx → partial `_rows.html`, sinon page complète
    """

    context_object_name = "products"
    template_name = "catalog/product_list.html"

    def get_queryset(self):
        return list_products(active_only=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ProductForm()
        return context

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            return ["catalog/partials/_rows.html"]
        return [self.template_name]


class ProductCreateView(CreateView):
    """Création staff — délègue au service (pas à form.save())."""

    form_class = ProductForm
    template_name = "catalog/product_form.html"
    success_url = reverse_lazy("catalog:product_list")

    def form_valid(self, form):
        create_product(**form.cleaned_data)
        if getattr(self.request, "htmx", False):
            return self.render_to_response(
                {"products": list_products(active_only=False)}
            )
        from django.shortcuts import redirect

        return redirect(self.success_url)

    def get_template_names(self):
        if getattr(self.request, "htmx", False) and self.request.method == "POST":
            return ["catalog/partials/_rows.html"]
        return [self.template_name]
```

### `templates/base.html` (CSRF HTMX)

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{% block title %}Back-office{% endblock %}</title>
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
</head>
<body>
  {% csrf_token %}
  <main id="main-content">{% block content %}{% endblock %}</main>
  <script>
    document.body.addEventListener("htmx:configRequest", function (event) {
      event.detail.headers["X-CSRFToken"] = "{{ csrf_token }}";
    });
  </script>
</body>
</html>
```

### Partial + page

```html
{# templates/catalog/partials/_rows.html #}
{% for p in products %}
<tr id="product-{{ p.id }}"><td>{{ p.name }}</td><td>{{ p.price }}</td></tr>
{% endfor %}
```

```html
{# templates/catalog/product_list.html #}
{% extends "base.html" %}
{% block content %}
<h1>Produits</h1>
<form hx-post="{% url 'catalog:product_create' %}"
      hx-target="#product-rows"
      hx-swap="innerHTML">
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit">Ajouter</button>
</form>
<table>
  <tbody id="product-rows">
    {% include "catalog/partials/_rows.html" %}
  </tbody>
</table>
{% endblock %}
```

> Pour un vrai formulaire de création, branche `ProductCreateView` sur un GET qui rend le formulaire, et garde le POST HTMX ci-dessus. L’important : **zéro** `Product.objects.create` dans la vue.

Ouvre : `http://127.0.0.1:8000/backoffice/products/`.

---

## 11. UI produit Astro {#combo-10}

Astro consomme **uniquement** `/api/...`. Aucune règle métier côté front. Secrets **jamais** dans `PUBLIC_*`.

Depuis `boutique/` :

```bash
cd frontend
npm create astro@latest . -- --template minimal --install --git false --typescript strict
```

### `frontend/.env`

```env
PUBLIC_API_URL=http://127.0.0.1:8000
```

En prod derrière Nginx same-origin : `PUBLIC_API_URL=` (chaîne vide) ou `https://www.exemple.com` — le navigateur appelle `/api` sans CORS.

### `frontend/src/lib/api/catalog.ts`

```typescript
const API = import.meta.env.PUBLIC_API_URL ?? "";

export type Product = {
  id: number;
  name: string;
  slug: string;
  price: string;
  is_active: boolean;
};

export async function listProducts(): Promise<Product[]> {
  const res = await fetch(`${API}/api/catalog/products`);
  if (!res.ok) throw new Error("API catalog indisponible");
  const data = await res.json();
  return data.items;
}
```

### `frontend/src/pages/index.astro`

```astro
---
import { listProducts } from "../lib/api/catalog";

let products = [];
let error = "";
try {
  products = await listProducts();
} catch (e) {
  error = e instanceof Error ? e.message : "Erreur API";
}
---
<html lang="fr">
  <head>
    <meta charset="utf-8" />
    <title>Boutique</title>
  </head>
  <body>
    <h1>Catalogue</h1>
    {error && <p>{error}</p>}
    <ul>
      {products.map((p) => (
        <li>{p.name} — {p.price} €</li>
      ))}
    </ul>
  </body>
</html>
```

Lancer (backend déjà sur `:8000`) :

```bash
cd frontend
npm run dev -- --port 4321
# → http://localhost:4321
```

**Frontière :** pas de CRUD staff dans Astro. Le back-office reste HTMX.

---

## 12. Celery + Redis {#combo-11}

Les tasks sont des **wrappers** : elles appellent un service, elles ne contiennent pas le métier.

### `config/celery.py`

```python
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

### `config/__init__.py`

```python
from .celery import app as celery_app

__all__ = ("celery_app",)
```

### `apps/catalog/tasks.py`

```python
from celery import shared_task

from apps.catalog.services import create_product


@shared_task
def create_product_async(name: str, slug: str, price: str) -> int:
    product = create_product(name=name, slug=slug, price=price)
    return product.id
```

Worker (hors Docker) :

```bash
uv run celery -A config worker -l info
```

Beat = **service séparé** si tu as des tâches planifiées. Ne jamais passer `--beat` sur le worker.

Tests : `CELERY_TASK_ALWAYS_EAGER=True` dans pytest.

---

## 13. Docker Compose (dev) {#combo-12}

Contexts : `./backend` et `./frontend` — **jamais** `build: .` à la racine.

### `backend/.dockerignore`

```
.venv
__pycache__
*.pyc
.git
staticfiles
db.sqlite3
```

### `backend/Dockerfile`

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm AS runner
RUN groupadd -r app && useradd -r -g app -d /app app
WORKDIR /app
COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/')"
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

En **dev**, Compose override la commande par `runserver` (voir plus bas).

### `frontend/Dockerfile`

```dockerfile
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

FROM deps AS build
COPY . .
ARG PUBLIC_API_URL
ENV PUBLIC_API_URL=$PUBLIC_API_URL
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
RUN addgroup -S app && adduser -S app -G app
COPY --from=build --chown=app:app /app/dist ./dist
COPY --from=build --chown=app:app /app/node_modules ./node_modules
COPY --from=build --chown=app:app /app/package.json ./
USER app
ENV HOST=0.0.0.0 PORT=4321 NODE_ENV=production
EXPOSE 4321
CMD ["node", "./dist/server/entry.mjs"]
```

> Adapter si Astro est en **static** : Nginx sert `dist/`, pas de runner Node.

### `.env.example` (racine du monorepo)

```env
DJANGO_SETTINGS_MODULE=config.settings.dev
DJANGO_SECRET_KEY=change-me-in-prod
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,backend
DATABASE_URL=postgres://app:dev@db:5432/app
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Astro — PUBLIC_* = exposable client, jamais de secrets
PUBLIC_API_URL=http://localhost:8000
```

Copie : `cp .env.example .env`

### `docker-compose.dev.yml` (racine)

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: app
      POSTGRES_PASSWORD: dev
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d app"]
      interval: 5s
      timeout: 3s
      retries: 10
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      retries: 10

  backend:
    build:
      context: ./backend
    command: uv run python manage.py runserver 0.0.0.0:8000
    volumes: [./backend:/app]
    env_file: [.env]
    environment:
      DATABASE_URL: postgres://app:dev@db:5432/app
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/1
      DJANGO_SETTINGS_MODULE: config.settings.dev
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }
    ports: ["8000:8000"]
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/')\""]
      interval: 15s
      retries: 5

  frontend:
    build:
      context: ./frontend
      target: deps
    command: npm run dev -- --host 0.0.0.0 --port 4321
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      PUBLIC_API_URL: http://localhost:8000
    depends_on:
      backend: { condition: service_healthy }
    ports: ["4321:4321"]

  worker:
    build: { context: ./backend }
    command: uv run celery -A config worker -l info
    volumes: [./backend:/app]
    env_file: [.env]
    environment:
      DATABASE_URL: postgres://app:dev@db:5432/app
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/1
      DJANGO_SETTINGS_MODULE: config.settings.dev
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }

volumes:
  pgdata:
```

### Premier `up` (ordre)

```bash
# 1. Verrouiller Python (obligatoire avant le build --frozen)
cd backend && uv lock && cd ..

# 2. Migrations : une fois le db healthy, dans un terminal
docker compose -f docker-compose.dev.yml up --build db redis
docker compose -f docker-compose.dev.yml run --rm backend uv run python manage.py migrate

# 3. Stack complète
docker compose -f docker-compose.dev.yml up --build
```

Smoke :

| URL | Attendu |
| :--- | :--- |
| `http://127.0.0.1:8000/health/` | `ok` |
| `http://127.0.0.1:8000/api/docs` | Swagger Ninja |
| `http://127.0.0.1:8000/backoffice/products/` | HTMX staff |
| `http://localhost:4321` | Catalogue Astro |

**Ne jamais** mettre `migrate` dans le `CMD` du conteneur web.

---

## 14. Nginx prod (schéma) {#combo-13}

Same-origin : le navigateur n’a plus besoin de CORS.

```nginx
# nginx/nginx.conf (extrait)
server {
    listen 443 ssl;
    server_name www.exemple.com;

    location /api/ {
        proxy_pass http://backend:8000;
    }
    location /backoffice/ {
        proxy_pass http://backend:8000;
    }
    location /admin/ {
        proxy_pass http://backend:8000;
    }
    location / {
        proxy_pass http://frontend:4321;
    }
}
```

| Chemin | Backend |
| :--- | :--- |
| `/` | Astro |
| `/api/` | Django Ninja |
| `/backoffice/` + `/admin/` | Django HTMX / admin |

---

## 15. Auth, CORS, secrets {#combo-14}

### JWT (clients Astro / mobile)

```python
from ninja.security import HttpBearer


class AuthBearer(HttpBearer):
    def authenticate(self, request, token: str):
        user = validate_jwt(token)  # ton service auth
        return user or None


@router.get("/me", auth=AuthBearer())
def me(request):
    return request.auth
```

En prod, préférer **cookies same-origin** via Nginx plutôt que d’exposer le token dans `PUBLIC_*`.

### Permission métier

La permission objet se vérifie **dans le service**, pas dans le router. L’endpoint transmet `request.user`.

### CORS (dev seulement, Astro sur :4321)

Déjà dans `dev.py` : `CORS_ALLOWED_ORIGINS = ["http://localhost:4321"]`.
Prod same-origin → CORS inutile pour le navigateur.

### Secrets

| OK | Interdit |
| :--- | :--- |
| `DJANGO_SECRET_KEY` dans `.env` (gitignoré) | Secret dans le repo |
| `PUBLIC_API_URL=http://localhost:8000` | Token / mot de passe dans `PUBLIC_*` |

---

## 16. Tests {#combo-15}

Ninja s’appuie sur le client de test Django :

```python
import pytest
from ninja.testing import TestClient

from config.api import api

client = TestClient(api)


@pytest.mark.django_db
def test_create_product():
    res = client.post(
        "/catalog/products",
        json={"name": "T-shirt", "slug": "t-shirt", "price": "19.99"},
    )
    assert res.status_code == 201
    assert res.json()["slug"] == "t-shirt"
```

```bash
uv add --dev pytest pytest-django
uv run pytest apps/catalog -q
```

Minimum par service : **happy path + 1 edge + 1 failure**.
Chaque endpoint : test d’autorisation (refus + succès).

---

## 17. Ninja vs DRF {#combo-16}

| Critère | Django Ninja | DRF |
| :--- | :--- | :--- |
| Typage / IDE | Pydantic natif | Serializers, moins strict |
| OpenAPI | Généré automatiquement | Via `drf-spectacular` etc. |
| Courbe d’apprentissage | Légère si Pydantic connu | Écosystème très large |
| Combo 2026 | **API JSON du monorepo** | Legacy uniquement |

**Recommandation :**

- **UI produit** → Astro → Ninja
- **UI staff** → CBV + HTMX → **mêmes** services
- **API JSON** → Django Ninja
- DRF seulement pour une dette existante ; ne pas dupliquer la même ressource sur les deux

---

## 18. Checklist plug-and-play {#combo-17}

À cocher dans l’ordre :

1. [ ] `uv --version` + `node -v` + `docker compose version`
2. [ ] `backend/` : `uv init`, `uv add`, `startproject config .`
3. [ ] Settings `base` / `dev` / `prod` + `DATABASE_URL`
4. [ ] `/health/` répond `ok`
5. [ ] Apps `catalog` + `orders` (models → selectors → services → schemas → api)
6. [ ] `api.add_router(...)` + `/api/docs` s’ouvre
7. [ ] Back-office HTMX sous `/backoffice/` (CBV, CSRF, partials)
8. [ ] `frontend/` Astro + `PUBLIC_API_URL` + page catalogue
9. [ ] `uv lock` puis `docker compose -f docker-compose.dev.yml up --build`
10. [ ] migrate **hors** CMD web ; worker Celery séparé
11. [ ] Aucun secret dans `PUBLIC_*` ; Next.js absent

---

## 19. Résumé {#combo-18}

| Objectif | Où ça vit |
| :--- | :--- |
| Instance API + OpenAPI | `backend/config/api.py` |
| Montage `/api/` | `backend/config/urls.py` |
| Endpoints par domaine | `backend/apps/<app>/api.py` |
| Contrats JSON | `backend/apps/<app>/schemas.py` |
| Lecture BDD | `backend/apps/<app>/selectors.py` |
| Écriture / règles métier | `backend/apps/<app>/services.py` |
| Back-office staff | CBV + `templates/` HTMX |
| Site produit | `frontend/` Astro |
| Compose dev | `docker-compose.dev.yml` |

**Commandes utiles :**

```bash
# Backend local
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
# → http://127.0.0.1:8000/api/docs
# → http://127.0.0.1:8000/backoffice/products/

# Frontend local
cd frontend
npm run dev -- --port 4321

# Stack Docker
docker compose -f docker-compose.dev.yml up --build
```

**Nouvelle app API :**

1. `startapp` dans `apps/` (models, schemas, selectors, services, api, views CBV, tasks).
2. Ajouter dans `INSTALLED_APPS`.
3. `api.add_router("/mon-app", router)` dans `config/urls.py`.
4. Brancher les URLs HTMX staff si besoin.
5. Migrer, tester via `/api/docs`, écrire un `TestClient`.

---

*Voir aussi : [Django_uv_htmx.md](/docs/django-uv-htmx/) (attributs HTMX, CSRF, init `config/` + `apps/`) et [Django_uv_htmx.md#dj-1-git](/docs/django-uv-htmx/#dj-1-git) (dépendances Git avec uv).*
