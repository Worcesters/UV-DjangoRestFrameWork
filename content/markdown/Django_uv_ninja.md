# Django Ninja + uv — API type-safe (structure `config/` + `apps/`)

> **Stack :** Python 3.12+ | Django 6.x | Django Ninja | Pydantic v2 | uv  
> **Structure :** `config/` (projet) + `apps/app1`, `apps/app2` (métier)  
> **Règle d’or :** la logique métier vit dans **Services / Selectors**, jamais dans les routers API.

---

## Table des matières {#toc}

1. [Arborescence cible](#ninja-0)
2. [Installation avec uv](#ninja-1)
3. [Point d’entrée API (`config/`)](#ninja-2)
4. [Structure d’une app (`apps/app1`)](#ninja-3)
5. [Exemple complet — `catalog` (app1)](#ninja-4)
6. [Exemple complet — `orders` (app2)](#ninja-5)
7. [Assembler les routers](#ninja-6)
8. [Auth, permissions, erreurs](#ninja-7)
9. [Consommation front (Next.js)](#ninja-8)
10. [Tests rapides](#ninja-9)
11. [Ninja vs DRF — quand choisir quoi ?](#ninja-10)
12. [Résumé](#ninja-11)

---

## 1. Arborescence cible {#ninja-0}

Même découpage que le reste du projet : **pas de logique métier dans `config/`**.

```
projet/
├── manage.py
├── pyproject.toml
├── uv.lock
├── config/
│   ├── urls.py              # pages Django + montage /api/
│   ├── api.py               # NinjaAPI racine (instance unique)
│   ├── wsgi.py
│   └── settings/
│       ├── base.py
│       ├── dev.py
│       └── prod.py
├── apps/
│   ├── __init__.py
│   ├── catalog/             # app1 — lecture / catalogue produits
│   │   ├── models.py
│   │   ├── schemas.py       # entrées / sorties API (Pydantic)
│   │   ├── selectors.py     # lecture (querysets)
│   │   ├── services.py      # écriture (create, update, delete)
│   │   ├── api.py           # Router Ninja (orchestration fine)
│   │   └── admin.py
│   └── orders/              # app2 — commandes
│       ├── models.py
│       ├── schemas.py
│       ├── selectors.py
│       ├── services.py
│       ├── api.py
│       └── admin.py
└── templates/               # UI HTMX (optionnel, hors Ninja)
```

| Zone | Responsabilité |
| :--- | :--- |
| `config/api.py` | Crée `NinjaAPI`, doc OpenAPI, routers globaux, handlers d’erreur |
| `apps/*/api.py` | Endpoints HTTP : valide l’entrée, appelle Service/Selector, renvoie un schema |
| `apps/*/schemas.py` | Contrats JSON (Pydantic) — **pas** de logique métier |
| `apps/*/services.py` | Écriture, règles métier, transactions |
| `apps/*/selectors.py` | Lecture optimisée (`select_related`, filtres) |

---

## 2. Installation avec uv {#ninja-1}

```bash
uv add django-ninja
uv sync
```

Vérifier :

```bash
uv run python -c "import ninja; print(ninja.__version__)"
```

`INSTALLED_APPS` : **pas besoin** d’ajouter une app `ninja` — c’est une librairie, pas une app Django.

---

## 3. Point d’entrée API (`config/`) {#ninja-2}

### `config/api.py`

```python
from ninja import NinjaAPI

api = NinjaAPI(
    title="Mon API",
    version="1.0.0",
    description="API REST type-safe — apps/catalog + apps/orders",
    docs_url="/docs",          # Swagger UI → /api/docs
    openapi_url="/openapi.json",
)
```

### `config/urls.py`

```python
from django.contrib import admin
from django.urls import path

from config.api import api
from apps.catalog.api import router as catalog_router
from apps.orders.api import router as orders_router

api.add_router("/catalog", catalog_router, tags=["catalog"])
api.add_router("/orders", orders_router, tags=["orders"])

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),    # toutes les routes Ninja sous /api/
]
```

URLs finales :

| Méthode | URL | Action |
| :--- | :--- | :--- |
| `GET` | `/api/catalog/products` | Liste produits |
| `POST` | `/api/catalog/products` | Créer un produit |
| `GET` | `/api/catalog/products/{id}` | Détail produit |
| `POST` | `/api/orders` | Créer une commande |
| `GET` | `/api/docs` | Documentation interactive |

---

## 4. Structure d’une app (`apps/app1`) {#ninja-3}

Patron à répliquer dans chaque app exposant une API :

```text
apps/catalog/
├── models.py       # schéma BDD uniquement
├── schemas.py      # ProductIn, ProductOut, ProductListOut
├── selectors.py  # get_product(), list_products()
├── services.py   # create_product(), update_product()
└── api.py          # Router + endpoints (minces)
```

**Interdit dans `api.py` :** règles métier lourdes, boucles d’écriture, `Product.objects.create(...)` direct (sauf prototype jetable).

---

## 5. Exemple complet — `catalog` (app1) {#ninja-4}

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

Enregistrer l’app dans `config/settings/base.py` :

```python
INSTALLED_APPS = [
    # ...
    "apps.catalog",
    "apps.orders",
]
```

Puis :

```bash
uv run python manage.py makemigrations catalog
uv run python manage.py migrate
```

---

## 6. Exemple complet — `orders` (app2) {#ninja-5}

`orders` **consomme** `catalog` via les services (pas via HTTP interne).

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
        )
        .get(pk=order_id)
    )


def order_total(*, order: Order) -> Decimal:
    return sum((line.unit_price * line.quantity for line in order.lines.all()), Decimal("0"))
```

### `apps/orders/api.py`

```python
from ninja import Router
from ninja.errors import HttpError

from apps.orders import services
from apps.orders.models import Order
from apps.orders.schemas import OrderIn, OrderOut, OrderLineOut
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

---

## 7. Assembler les routers {#ninja-6}

Tout passe par **une seule** instance `NinjaAPI` :

```python
# config/api.py
from ninja import NinjaAPI

api = NinjaAPI(title="Mon API", version="1.0.0")
```

```python
# config/urls.py
from config.api import api
from apps.catalog.api import router as catalog_router
from apps.orders.api import router as orders_router

api.add_router("/catalog", catalog_router, tags=["catalog"])
api.add_router("/orders", orders_router, tags=["orders"])

urlpatterns = [
  path("api/", api.urls),
]
```

**Versionner** (optionnel) :

```python
api_v1 = NinjaAPI(version="1.0.0", urls_namespace="api-v1")
api_v1.add_router("/catalog", catalog_router)
# path("api/v1/", api_v1.urls)
```

---

## 8. Auth, permissions, erreurs {#ninja-7}

### Auth JWT (schéma type front Next.js)

```python
from ninja.security import HttpBearer


class AuthBearer(HttpBearer):
    def authenticate(self, request, token: str):
        user = validate_jwt(token)  # votre service auth
        return user or None


@router.get("/me", auth=AuthBearer(), response=UserOut)
def me(request):
    return request.auth
```

### Permission Django

```python
from ninja.errors import HttpError


@router.post("/products", response={201: ProductOut})
def products_create(request, payload: ProductIn):
    if not request.user.is_staff:
        raise HttpError(403, "Accès refusé")
    ...
```

### Handler d’erreur global

```python
# config/api.py
from ninja.errors import HttpError

@api.exception_handler(ProductAlreadyExistsError)
def on_duplicate(request, exc):
    return api.create_response(request, {"detail": str(exc)}, status=409)
```

---

## 9. Consommation front (Next.js) {#ninja-8}

### Server Component (fetch)

```typescript
const API = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

export async function getProducts() {
  const res = await fetch(`${API}/api/catalog/products`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) throw new Error("API catalog indisponible");
  return res.json();
}
```

### Client (mutation)

```typescript
await fetch(`${API}/api/orders`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "client@example.com",
    lines: [{ product_id: 1, quantity: 2 }],
  }),
});
```

### CORS (`config/settings/dev.py`)

```python
INSTALLED_APPS += ["corsheaders"]
MIDDLEWARE.insert(1, "corsheaders.middleware.CorsMiddleware")
CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
```

```bash
uv add django-cors-headers
```

---

## 10. Tests rapides {#ninja-9}

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
uv run pytest apps/catalog/tests/test_api.py -q
```

---

## 11. Ninja vs DRF — quand choisir quoi ? {#ninja-10}

| Critère | Django Ninja | DRF |
| :--- | :--- | :--- |
| Typage / IDE | Pydantic natif, excellent | Serializers, moins strict |
| OpenAPI | Généré automatiquement | Via `drf-spectacular` etc. |
| Courbe d’apprentissage | Légère si Pydantic connu | Écosystème très large |
| ViewSets / admin API | Routers simples | ViewSets matures |
| Projet actuel (HTMX + API) | **API JSON moderne** | Déjà en place, OK pour legacy |

**Recommandation projet 2026 :**

- **Pages HTML / HTMX** → vues Django classiques (`views.py`).
- **API front Next.js / mobile** → **Django Ninja** + Service Layer.
- Coexistence Ninja + DRF possible le temps d’une migration ; éviter de dupliquer la même ressource sur les deux.

---

## 12. Résumé {#ninja-11}

| Objectif | Où ça vit |
| :--- | :--- |
| Instance API + OpenAPI | `config/api.py` |
| Montage `/api/` | `config/urls.py` |
| Endpoints par domaine | `apps/<app>/api.py` |
| Contrats JSON | `apps/<app>/schemas.py` |
| Lecture BDD | `apps/<app>/selectors.py` |
| Écriture / règles métier | `apps/<app>/services.py` |
| Schéma BDD | `apps/<app>/models.py` |

**Commandes utiles :**

```bash
uv add django-ninja
uv run python manage.py migrate
uv run python manage.py runserver
# → http://127.0.0.1:8000/api/docs
```

**Checklist nouvelle app API :**

1. Créer `apps/mon_app/` (models, schemas, selectors, services, api).
2. Ajouter dans `INSTALLED_APPS`.
3. `api.add_router("/mon-app", router)` dans `config/urls.py`.
4. Migrer, tester via `/api/docs`, écrire un test `TestClient`.

---

*Voir aussi : [Django_uv_htmx.md](/docs/django-uv-htmx/) (structure `config/` + `apps/`, uv, HTMX) et [Django_uv_htmx.md#dj-1-git](/docs/django-uv-htmx/#dj-1-git) (dépendances Git avec uv).*
