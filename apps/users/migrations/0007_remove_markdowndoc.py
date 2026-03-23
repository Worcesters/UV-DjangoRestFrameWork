# Suppression du modèle MarkdownDoc : les documents sont lus depuis content/markdown/ (fichiers).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_user_add_societe"),
    ]

    operations = [
        migrations.DeleteModel(
            name="MarkdownDoc",
        ),
    ]
