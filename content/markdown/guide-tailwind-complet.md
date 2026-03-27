# Tailwind CSS {#tailwind-css}

> **Version utilisée dans ce dépôt :** Tailwind CSS **3.4** (`package.json`).
> **Fichier généré :** `static/css/tailwind.css` à partir de `static/css/tailwind.input.css`.
> **Config :** `tailwind.config.js` à la racine du projet.

---

## Table des matières {#toc}

1. [Qu’est-ce que Tailwind ?](#tw-1)
2. [Installation et build dans ce projet](#tw-2)
3. [Comment ça marche : utilitaires et JIT](#tw-3)
4. [Structure d’une classe](#tw-4)
5. [Espacement et tailles](#tw-5)
6. [Couleurs](#tw-6)
7. [Typographie](#tw-7)
8. [Bordures, ombres, rayons](#tw-8)
9. [Flexbox](#tw-9)
10. [CSS Grid](#tw-10)
11. [Positionnement](#tw-11)
12. [Responsive : préfixes `sm:` `md:` `lg:` …](#tw-12)
13. [États : `hover`, `focus`, `active`, etc.](#tw-13)
14. [Mode sombre `dark:` (optionnel)](#tw-14)
15. [Valeurs arbitraires `[]`](#tw-15)
16. [Transparence et opacité](#tw-16)
17. [Arrière-plans et dégradés](#tw-17)
18. [Transitions et animations](#tw-18)
19. [Visibilité et accessibilité](#tw-19)
20. [Personnalisation : `tailwind.config.js`](#tw-20)
21. [Couche `@layer` et `@apply` (usage modéré)](#tw-21)
22. [Tailwind + Django (templates et formulaires)](#tw-22)
23. [Pièges fréquents et dépannage](#tw-23)
24. [Ressources officielles](#tw-24)

---

## 1) Qu’est-ce que Tailwind ? {#tw-1}

**Tailwind CSS** est un framework **utility-first** : au lieu d’écrire des feuilles de style avec des noms de classes sémantiques (`.card`, `.btn-primary`), on compose l’interface avec de **petites classes utilitaires** (`flex`, `p-4`, `text-center`, `bg-blue-500`).

**Avantages :**
- itération rapide dans le HTML ;
- cohérence des design tokens (échelle d’espacements, couleurs) ;
- moins de CSS personnalisé à maintenir.

**Inconvénient :** le HTML peut être verbeux ; on compense avec des **composants** (partials Django, includes) ou `@apply` ponctuel.

---

## 2) Installation et build dans ce projet {#tw-2}

Les dépendances front sont dans `package.json`. Les commandes utiles :

| Commande | Rôle |
| :--- | :--- |
| `npm run build:css` | Compile **une fois** `tailwind.input.css` → `tailwind.css` (minifié). |
| `npm run watch:css` | Recompile **à chaque sauvegarde** (développement). |

**Entrée / sortie (script `build:css`) :**
- **Entrée :** `./static/css/tailwind.input.css` (contient `@tailwind base/components/utilities`).
- **Sortie :** `./static/css/tailwind.css` (fichier référencé dans `base.html`).

Après avoir ajouté de **nouvelles** classes dans des templates ou des chaînes Python, **relance le build** pour qu’elles apparaissent dans `tailwind.css`.

---

## 3) Comment ça marche : utilitaires et JIT {#tw-3}

Tailwind v3 utilise le **JIT** (Just-In-Time) : les classes sont **générées à la volée** en fonction du scan des fichiers listés dans `content` de `tailwind.config.js`.

Dans ce dépôt, le scan inclut notamment :

- `./templates/**/*.html`
- `./apps/**/templates/**/*.html`
- `./apps/**/*.py` (utile si des classes apparaissent dans des chaînes Python)
- `./static/**/*.js`

Si une classe est **absente** du CSS final, le style ne s’appliquera pas (voir [§23](#tw-23)).

---

## 4) Structure d’une classe {#tw-4}

Exemples :

| Classe | Signification |
| :--- | :--- |
| `p-4` | padding sur les 4 côtés, taille **4** sur l’échelle Tailwind |
| `px-6` | padding horizontal |
| `mt-2` | margin-top |
| `text-lg` | taille de police |
| `font-bold` | graisse |
| `text-slate-700` | couleur du texte (palette **slate**, nuance **700**) |
| `bg-white` | fond blanc |
| `rounded-xl` | border-radius large |
| `shadow-md` | ombre moyenne |

Les **variantes** se préfixent : `hover:bg-blue-600`, `md:text-xl`, `focus:ring-2`.

---

## 5) Espacement et tailles {#tw-5}

**Échelle** : `0`, `px`, `0.5`, `1`, `1.5`, `2` … jusqu’à des valeurs grandes (`96`, etc.). Souvent **1 unité ≈ 0.25rem (4px)** sauf cas particuliers.

| Préfixe | Propriété |
| :--- | :--- |
| `m-*` | margin |
| `mx-*` / `my-*` | margin horizontal / vertical |
| `mt-*`, `mr-*`, `mb-*`, `ml-*` | margin par côté |
| `p-*` | padding (idem variantes `px`, `py`, `pt`…) |

**Largeur / hauteur :** `w-full`, `w-1/2`, `max-w-md`, `min-h-screen`, `h-12`, etc.

---

## 6) Couleurs {#tw-6}

Modèle : **`{propriété}-{couleur}-{nuance}`**.

Exemples de **couleurs** : `slate`, `gray`, `red`, `blue`, `teal`, `emerald`, `violet`, `indigo`, etc.

**Nuances** : `50` (très clair) à `950` (très foncé), selon la palette.

Exemples :
- `bg-teal-600`, `text-white`, `border-slate-200`
- `text-blue-600/80` : opacité **80%** (voir [§16](#tw-16))

---

## 7) Typographie {#tw-7}

| Classe | Effet |
| :--- | :--- |
| `text-xs` … `text-9xl` | tailles prédéfinies |
| `font-thin` … `font-black` | graisse |
| `italic`, `not-italic` | style |
| `leading-tight`, `leading-relaxed` | interligne |
| `tracking-tight`, `tracking-widest` | interlettrage |
| `text-left`, `text-center`, `text-right`, `text-justify` | alignement |
| `uppercase`, `lowercase`, `capitalize` | casse |
| `truncate`, `line-clamp-*` | débordement / nombre de lignes |

---

## 8) Bordures, ombres, rayons {#tw-8}

| Classe | Effet |
| :--- | :--- |
| `border`, `border-2`, `border-t`, … | bordures |
| `border-slate-200` | couleur de bordure |
| `rounded`, `rounded-lg`, `rounded-full` | rayons |
| `shadow`, `shadow-sm`, `shadow-lg`, `shadow-xl` | ombres portées |
| `ring-2`, `ring-teal-500`, `ring-offset-2` | anneaux (focus accessibles) |

---

## 9) Flexbox {#tw-9}

Conteneur : `flex`, `inline-flex`.

Direction : `flex-row`, `flex-col`, `flex-row-reverse`.

Alignement :
- `items-start` | `items-center` | `items-end` | `items-stretch` (axe **transversal**)
- `justify-start` | `justify-center` | `justify-between` | `justify-end` (axe **principal**)

Enfants : `flex-1`, `shrink-0`, `grow`, `basis-*`, `gap-*`.

---

## 10) CSS Grid {#tw-10}

Conteneur : `grid`, `grid-cols-1`, `grid-cols-12`, `gap-4`.

Placement : `col-span-2`, `col-start-2`, `row-span-*`.

Exemple fréquent : `grid grid-cols-1 md:grid-cols-2 gap-6`.

---

## 11) Positionnement {#tw-11}

`relative`, `absolute`, `fixed`, `sticky` + `top-*`, `right-*`, `inset-*`, `z-10`, `z-50`, etc.

---

## 12) Responsive : préfixes `sm:` `md:` `lg:` … {#tw-12}

Tailwind est **mobile-first** : une classe sans préfixe s’applique à **toutes** les largeurs ; les préfixes ajoutent des règles **à partir du breakpoint**.

Breakpoints par défaut (v3) :

| Préfixe | Min width |
| :--- | :--- |
| `sm:` | 640px |
| `md:` | 768px |
| `lg:` | 1024px |
| `xl:` | 1280px |
| `2xl:` | 1536px |

Exemple : `class="text-sm md:text-base lg:text-lg"` — la taille augmente sur écrans plus larges.

---

## 13) États : `hover`, `focus`, `active`, etc. {#tw-13}

| Variante | Usage |
| :--- | :--- |
| `hover:` | survol souris |
| `focus:` | focus clavier / souris |
| `focus-visible:` | focus clavier (souvent préférable pour l’accessibilité) |
| `active:` | pendant le clic |
| `disabled:` | élément désactivé |
| `group` / `group-hover:` | état sur un parent |

Exemple : `focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500`.

---

## 14) Mode sombre `dark:` (optionnel) {#tw-14}

Si tu actives le mode sombre (stratégie `class` ou `media` dans la config), tu peux préfixer avec `dark:` :

`bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100`

*(Non activé par défaut dans ce projet — à ajouter si besoin.)*

---

## 15) Valeurs arbitraires `[]` {#tw-15}

Quand la palette ne suffit pas :

- `w-[13rem]`, `top-[17px]`, `bg-[#0ea5e9]`, `grid-cols-[200px_1fr]`

À utiliser avec parcimonie pour garder la cohérence des design tokens.

---

## 16) Transparence et opacité {#tw-16}

- `bg-black/50` — fond noir à 50 % d’opacité
- `text-slate-600/80` — texte avec alpha

Fonctionne avec **slash + nombre** sur les couleurs de la palette.

---

## 17) Arrière-plans et dégradés {#tw-17}

- `bg-gradient-to-r`, `bg-gradient-to-br`
- `from-teal-500`, `via-cyan-500`, `to-blue-600`

**Attention :** si le build ne contient pas ces classes (fichier non scanné, ou oubli de `npm run build:css`), le rendu peut “disparaître” ou sembler blanc — d’où l’intérêt d’un **fond de secours** en CSS classique pour les boutons critiques (comme sur la page contact).

---

## 18) Transitions et animations {#tw-18}

- `transition`, `duration-300`, `ease-in-out`
- `hover:scale-105`, `active:scale-95`
- Animations utilitaires : `animate-spin`, `animate-pulse`, etc.

---

## 19) Visibilité et accessibilité {#tw-19}

- `sr-only` — texte lisible par les lecteurs d’écran, caché visuellement
- `aria-*` — attributs HTML (pas Tailwind, mais à combiner)
- `focus-visible:ring-*` — contours de focus visibles au clavier

---

## 20) Personnalisation : `tailwind.config.js` {#tw-20}

Dans ce projet :

- **`content`** : fichiers scannés pour le JIT (voir [§3](#tw-3)).
- **`theme.extend`** : étendre couleurs, fonts, breakpoints sans écraser toute la config.
- **`safelist`** : **forcer** la génération de classes **dynamiques** ou **invisibles au scanner** — ici des classes `file:*` pour les widgets de fichiers Django.

Exemple d’extension (illustratif) :

```js
theme: {
  extend: {
    colors: { brand: { 500: "#0ea5e9" } },
    fontFamily: { sans: ["Plus Jakarta Sans", "sans-serif"] },
  },
},
```

---

## 21) Couche `@layer` et `@apply` (usage modéré) {#tw-21}

Dans un fichier CSS traité par Tailwind (ex. un fichier importé via `@tailwind` ou `@import`), on peut écrire :

```css
@layer components {
  .btn-primary {
    @apply rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700;
  }
}
```

**Recommandation :** réserver `@apply` aux **vrais composants répétés** ; sinon préférer les utilitaires dans le HTML (ou des partials Django).

---

## 22) Tailwind + Django (templates et formulaires) {#tw-22}

**Templates :** classes directement dans `class="..."` — idéal pour le scanner.

**Formulaires Django (`forms.py`) :** les classes sont souvent dans des **chaînes Python** (`attrs={"class": "..."}`). Tant que le fichier `.py` est dans `content` (`./apps/**/*.py` ici), le JIT peut les voir — mais en cas de construction dynamique de classes (concaténation, f-strings complexes), utiliser **`safelist`** ou des classes **statiques** connues.

**Fichiers CSS complémentaires** (`static/css/base.css`, `static/css/contact/page.css`) : styles **hors Tailwind** ou **surcharges** ciblées (ex. bouton avec couleur hex explicite).

---

## 23) Pièges fréquents et dépannage {#tw-23}

| Symptôme | Cause probable | Piste |
| :--- | :--- | :--- |
| Classe sans effet | Classe absente du build | `npm run build:css` ; vérifier le chemin dans `content` |
| Styles “qui sautent” après déploiement | Oubli de rebuild / mauvais `STATIC_ROOT` | Rebuild avant `collectstatic` |
| Classes dans chaînes JS non listées | Fichier hors `content` | Ajouter le fichier ou `safelist` |
| Widget Django dynamique | Concaténation de noms de classes | `safelist` ou liste fermée de classes |
| Texte blanc invisible | Fond non généré + `text-white` | Fond explicite ou couleur de secours en CSS |
| `hover:` ne marche pas sur mobile | Certaines interactions tactiles | Tester `active:` ou `@media (hover:hover)` |

---

## 24) Ressources officielles {#tw-24}

- **Documentation :** [https://tailwindcss.com/docs](https://tailwindcss.com/docs)
- **Recherche de classes :** barre de recherche sur le site officiel
- **Playground :** [https://play.tailwindcss.com](https://play.tailwindcss.com)

---

*Document généré pour le dépôt **uv-django** — à tenir à jour si la version de Tailwind ou les scripts npm changent.*
