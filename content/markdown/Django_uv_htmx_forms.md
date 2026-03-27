# HTMX & Django Form

> Objectif : comprendre comment utiliser HTMX pour rendre un formulaire Django **interactif** (affichage conditionnel de champs, re-rendu partiel, gestion des erreurs `form.is_valid()`).

---

## Table des matières {#toc}

1. [Rappels HTMX : fragment + cible](#hf-1)
2. [Django forms : la validation se fait côté serveur](#hf-2)
3. [Architecture recommandée (Templates)](#hf-3)
4. [Exemple : champ dynamique après `societe`](#hf-4)
5. [GET vs POST : choisir selon l’interaction](#hf-5)
6. [Pièges fréquents](#hf-6)
7. [Mini checklist](#hf-7)

---

## 1) Rappels HTMX : fragment + cible {#hf-1}

Avec HTMX, l’idée est toujours la même :
1. Un élément HTML déclenche une requête HTTP (souvent `hx-get` ou `hx-post`).
2. Le serveur renvoie un **fragment HTML**.
3. HTMX injecte ce fragment dans un élément de la page via `hx-target` et `hx-swap`.

Les attributs les plus importants :

- `hx-get="/url/"` : déclenche une requête **GET**.
- `hx-post="/url/"` : déclenche une requête **POST**.
- `hx-target="#id"` : injecte le résultat dans l’élément ayant cet id (ou plus généralement le sélecteur).
- `hx-swap="innerHTML"` : remplace **le contenu interne** de la cible.
- `hx-swap="outerHTML"` : remplace **la cible** entière (balise incluse).
- `hx-trigger="change"` / `hx-trigger="keyup changed delay:300ms"` : précise sur quel événement déclencher.

## 2) Django forms : la validation se fait côté serveur {#hf-2}

Un formulaire Django :
 - définit les champs et règles (required, validators, `clean_<champ>`, `clean()`).
 - au POST : tu crées `form = ContactForm(request.POST)` puis `form.is_valid()`.

En cas d’erreur, `form.errors` est rempli et ton template peut afficher :
 - `field.errors.0` pour un champ
 - `form.non_field_errors` pour des erreurs globales

Ce point est crucial : **HTMX ne remplace pas la validation**. HTMX remplace seulement l’UX (re-rendu partiel / sans rechargement complet).

---

## 3) Architecture recommandée (Templates) {#hf-3}

### A) Page “globale” + bloc de contenu
Ta page (ex: `templates/contact/page.html`) contient une zone extensible :

```django
{% block contact_form %}
  <!-- placeholder / skeleton -->
{% endblock %}
```

### B) Template “formulaire” enfant qui remplit le bloc
Un template enfant (ex: `templates/contact/form.html`) fait :

```django
{% extends "contact/page.html" %}

{% block contact_form %}
  <form ...>
    {% csrf_token %}
    {% for field in form %}
      {{ field }}
    {% endfor %}
  </form>
{% endblock %}
```

Ensuite, **la vue** doit rendre la template enfant pour que le bloc soit rempli.

---

## 4) Exemple : champ dynamique après `societe` (`site_web` + fragment HTMX) {#hf-4}

### Cas d’usage
Quand l’utilisateur tape dans `societe`, un `hx-get` charge un fragment qui affiche un **nouveau champ** `site_web` (rendu par Django, même style Tailwind que les autres widgets).

### Étape 0 : champ côté `ContactForm`
- Ajouter `site_web = forms.URLField(required=False, widget=...)`.
- Dans le template du formulaire principal, **ne pas** afficher `site_web` dans la boucle `{% for field in form %}` (sinon il serait toujours visible). Ex. `{% if field.name != "site_web" %}…{% endif %}`.

### Étape 1 : cible vide dans le `<form>`
Dans `templates/contact/form.html` :

```django
<div id="societe-extra" class="mt-3"></div>
```

Option recommandée : `hx-boost="false"` sur le `<form>` pour éviter que le boost global du `<body>` interfère avec des interactions fines (navigation vs fragment).

### Étape 2 : déclencher HTMX depuis le widget `societe`
Dans `apps/contact/form.py`, sur le `TextInput` de `societe` :

```python
widget=forms.TextInput(attrs={
    "hx-get": "/contact/societe-extra/",
    "hx-target": "#societe-extra",
    "hx-select": "#htmx-societe-fragment",
    "hx-swap": "innerHTML",
    "hx-push-url": "false",
    "hx-trigger": "keyup changed delay:300ms",
})
```

**Pourquoi `hx-select` est indispensable ici :** si `base.html` définit sur le `<body>` quelque chose comme `hx-select="#main-content"` (souvent avec `hx-boost="true"`), HTMX **hérite** de ce sélecteur. Une réponse fragment **sans** `#main-content` donne alors un **swap vide** : le champ ne s’affiche jamais, alors que l’URL `GET /contact/societe-extra/?societe=…` renvoie bien du HTML quand on l’ouvre dans le navigateur.

La réponse fragment doit donc contenir un élément racine avec un id fixe (ex. `#htmx-societe-fragment`), et le déclencheur doit redéfinir `hx-select` vers cet id.

**Pourquoi `hx-push-url="false"` :** si le `<body>` a `hx-push-url="true"`, HTMX peut mettre à jour la barre d’adresse avec l’URL du fragment (`/contact/societe-extra/?societe=…`). Un **F5** recharge alors cette URL au lieu de `/contact/`. Désactiver le push sur le déclencheur évite ce comportement.

### Étape 3 : vue fragment
Vue du type `ContactSocieteExtraView` qui construit un `ContactForm(initial={"societe": societe})` et rend `partials/societe_extra.html` avec `{"show": show, "societe": societe, "form": form}`.

### Étape 4 : partiel HTML
`templates/partials/societe_extra.html` : envelopper le contenu dans `#htmx-societe-fragment` et rendre `{{ form.site_web }}` :

```django
{% if show %}
<div id="htmx-societe-fragment">
  <label for="{{ form.site_web.id_for_label }}">{{ form.site_web.label }}</label>
  {{ form.site_web }}
</div>
{% endif %}
```

---

## 5) GET vs POST : choisir selon l’interaction {#hf-5}

- Pour “afficher un bloc” après saisie : **GET** (`hx-get`).
- Pour “soumettre le formulaire” : **POST** (`hx-post`), généralement avec :
  - `hx-target` (sur quel morceau injecter)
  - un `hx-swap` adapté (souvent `outerHTML` sur un wrapper)
  - et gestion CSRF (avec ton hook `htmx:configRequest` ou `{% csrf_token %}`).

---

## 6) Pièges fréquents {#hf-6}

1. **Mauvaise cible** (`hx-target`) ou mauvais `hx-swap` :
   - `innerHTML` injecte à l’intérieur de l’élément
   - `outerHTML` remplace la balise entière

2. **Cible absente dans la réponse** :
   - si ton template renvoie une page complète alors que HTMX attend un fragment, utilise `hx-select` ou renvoie directement le fragment.

3. **Le bloc injecté doit être dans le même `<form>`** :
   - si tu injectes un champ qui doit être envoyé au submit final, assure-toi qu’il se retrouve bien dans le `<form>` au moment de soumission.

4. **`hx-boost`** :
   - si ton layout booste tout (ex: `hx-boost="true"` sur le `body`), pense à désactiver (`hx-boost="false"`) sur certaines actions (ex: logout) ou à redéfinir `hx-target` / `hx-select`.

---

## 7) Mini checklist {#hf-7}

- Je déclenche sur `change` / `keyup` / `delay` selon le besoin.
- Je mets `hx-target` vers un conteneur vide existant.
- Le endpoint renvoie un fragment HTML.
- La validation (`form.is_valid()`) reste côté Django.
- Si un champ injecté doit être soumis au submit final, il est réellement dans le `<form>`.

