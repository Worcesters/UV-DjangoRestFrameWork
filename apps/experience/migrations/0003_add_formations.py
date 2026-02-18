from django.db import migrations

def add_formations_data(apps, schema_editor):
    Experience = apps.get_model('experience', 'Experience')

    # Ajout des formations selon ton CV [cite: 6]
    formations = [
        {
            "titre": "Développeur en Intelligence Artificielle (Bac+3)",
            "entreprise": "3W Academy Paris",
            "description": "Spécialisation : PYTHON, PANDAS, NUMPY, AGILE, KERAS. [cite: 7, 9]",
            "date_debut": "Octobre 2021",
            "date_fin": "Septembre 2022",
            "pos_x": 25, "pos_z": -25, "hauteur": 10, "couleur_hex": "#f59e0b"
        },
        {
            "titre": "Soft Skills",
            "entreprise": "ESILV La Défense",
            "description": "Communication, travail en équipe, initiation à la gestion de projet. [cite: 10, 11]",
            "date_debut": "Décembre 2017",
            "date_fin": "Avril 2018",
            "pos_x": -25, "pos_z": -5, "hauteur": 6, "couleur_hex": "#8b5cf6"
        }
    ]

    for f in formations:
        Experience.objects.create(**f)

class Migration(migrations.Migration):
    dependencies = [
        ('experience', '0002_seed_cv_data'), # Vérifie que le nom correspond à ta migration précédente
    ]

    operations = [
        migrations.RunPython(add_formations_data),
    ]