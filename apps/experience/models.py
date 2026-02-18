from django.db import models

class Experience(models.Model):
    titre = models.CharField(max_length=200)
    entreprise = models.CharField(max_length=200)
    description = models.TextField()
    date_debut = models.CharField(max_length=100)
    date_fin = models.CharField(max_length=100)
    # Position dans le monde 3D
    pos_x = models.FloatField()
    pos_z = models.FloatField()
    hauteur = models.FloatField(default=5.0)
    couleur_hex = models.CharField(max_length=7, default="#3b82f6")

    def __str__(self):
        return f"{self.entreprise} - {self.titre}"