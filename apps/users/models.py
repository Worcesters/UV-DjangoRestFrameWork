from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.text import slugify


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


class MarkdownDoc(models.Model):
    """Document Markdown : titre, description, contenu. Affiché en vignette sur l'accueil."""
    title = models.CharField("Titre", max_length=200)
    slug = models.SlugField(max_length=220, unique=True, allow_unicode=True, blank=True)
    description = models.CharField("Description", max_length=500, blank=True)
    content = models.TextField("Contenu Markdown", blank=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="markdown_docs",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Document Markdown"
        verbose_name_plural = "Documents Markdown"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or "doc"
            self.slug = base
            n = 1
            while MarkdownDoc.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base}-{n}"
                n += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
