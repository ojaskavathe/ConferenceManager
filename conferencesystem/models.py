from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone

from django.utils.translation import gettext_lazy as _

from phonenumber_field.modelfields import PhoneNumberField

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, phone, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        if not phone:
            raise ValueError('The given phone must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, phone, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, phone, password, **extra_fields)

    def create_superuser(self, email, phone, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, phone, password, **extra_fields)


class User(AbstractUser):
    """User model."""

    username = None
    email = models.EmailField(_('Email Address'), unique=True)
    phone = PhoneNumberField(blank=True, unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']

    objects = UserManager()
    
    def __str__(self):
        return self.email

class Conference(models.Model):
    title = models.CharField(max_length=255)
    organizing_institute = models.CharField(max_length=255)
    institute_details = models.TextField()
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.title
    
    def submissions_open(self):
        return timezone.now().date() <= self.end_date
    
    def is_chair(self, user):
        return self.chair_set.filter(user=user).exists()

class Track(models.Model):
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.title

class Chair(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    conferences = models.ManyToManyField(Conference)
    
    def __str__(self):
        return self.user.email

class Author(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    conferences = models.ManyToManyField(Conference)
    
    def __str__(self):
        return self.user.email

class Paper(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    title = models.CharField(max_length=255)
    abstract = models.TextField()
    file = models.FileField(upload_to='papers/')
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE)
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    authors = models.ManyToManyField(Author, related_name='papers')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')

    def __str__(self):
        return self.title
    
    def is_author(self, user):
        return self.authors.filter(user=user).exists()
    
    def is_reviewer(self, user):
        return self.reviewer_set.filter(user=user).exists()

class Reviewer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    papers = models.ManyToManyField(Paper)

    def __str__(self):
        return self.user.email

class Review(models.Model):
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(Reviewer, on_delete=models.CASCADE)
    score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comments = models.TextField()

    class Meta:
        unique_together = ['paper', 'reviewer']

    def __str__(self):
        return f"Review for {self.paper.title} by {self.reviewer.user.email}"