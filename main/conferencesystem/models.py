from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone

class Conference(models.Model):
    title = models.CharField(max_length=255)
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
        return self.user.username

class Author(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    conferences = models.ManyToManyField(Conference)
    
    def __str__(self):
        return self.user.username

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
        return self.user.username

class Review(models.Model):
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(Reviewer, on_delete=models.CASCADE)
    score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comments = models.TextField()

    class Meta:
        unique_together = ['paper', 'reviewer']

    def __str__(self):
        return f"Review for {self.paper.title} by {self.reviewer.user.username}"