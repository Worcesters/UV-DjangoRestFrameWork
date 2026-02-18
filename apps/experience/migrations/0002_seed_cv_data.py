from django.db import migrations

def create_initial_experiences(apps, schema_editor):
    Experience = apps.get_model('experience', 'Experience')

    # Données extraites de ton CV
    data = [
        {
            "titre": "Ingénieur d'études et développements",
            "entreprise": "Hitpart",
            "description": "Analyse du besoin fonctionnel, développement from scratch (Angular, Python/Django), Prompt engineering (LLM), Docker.",
            "date_debut": "Décembre 2022",
            "date_fin": "Présent",
            "pos_x": -15, "pos_z": -15, "hauteur": 14, "couleur_hex": "#3b82f6"
        },
        {
            "titre": "Développeur Full-Stack / Chef de projet",
            "entreprise": "Factoria",
            "description": "Création de projet from scratch, amélioration d'outils internes. Stack: Python, Vue.js, Django.",
            "date_debut": "Octobre 2021",
            "date_fin": "Septembre 2022",
            "pos_x": 15, "pos_z": -10, "hauteur": 9, "couleur_hex": "#6366f1"
        },
        {
            "titre": "Développeur informatique",
            "entreprise": "IWI Event",
            "description": "Intégration de solutions web/emailing, assistance technique événementielle. Stack: JavaScript, AngularJS.",
            "date_debut": "Novembre 2019",
            "date_fin": "Octobre 2020",
            "pos_x": 0, "pos_z": -25, "hauteur": 6, "couleur_hex": "#ec4899"
        },
        {
            "titre": "Développeur web / Chargé de projet",
            "entreprise": "Digifactory",
            "description": "Intégration HTML/CSS, gestion de projet et assistance technique.",
            "date_debut": "Avril 2018",
            "date_fin": "Décembre 2018",
            "pos_x": -15, "pos_z": -30, "hauteur": 5, "couleur_hex": "#10b981"
        }
    ]

    for item in data:
        Experience.objects.create(**item)

class Migration(migrations.Migration):
    dependencies = [
        ('experience', '0001_initial'), # Doit correspondre à ta migration initiale
    ]

    operations = [
        migrations.RunPython(create_initial_experiences),
    ]