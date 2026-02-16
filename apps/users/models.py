from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Crée un nouvel utilisateur
        Args:
            email: L'adresse email de l'utilisateur
            password: Le mot de passe de l'utilisateur
            **extra_fields: D'autres champs à ajouter
        Returns:
            L'utilisateur créé
        """
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crée un superutilisateur
        Args:
            email: L'adresse email de l'utilisateur
            password: Le mot de passe de l'utilisateur
            **extra_fields: D'autres champs à ajouter
        Returns:
            L'utilisateur créé
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password=password, **extra_fields)


class User(AbstractUser):
    """
    Modèle d'utilisateur personnalisé
    Args:
        AbstractUser: Modèle d'utilisateur de Django
    Returns:
        L'utilisateur créé
    """
    username = None
    email = models.EmailField("Email address", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def __str__(self):
        return self.email
