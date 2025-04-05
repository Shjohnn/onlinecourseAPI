from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import ManyToManyField

from core import settings


class User(AbstractUser):
    username=models.CharField(max_length=255,unique=True)
    password = models.CharField(max_length=10)
    email=models.EmailField()
    date_joined=models.DateField(auto_now_add=True)
    is_instructor=models.BooleanField(default=False)

    def __str__(self):
        return self.username


class Course(models.Model):
    title=models.CharField(max_length=255)
    description=models.CharField(max_length=255)
    price=models.PositiveSmallIntegerField()
    instructor=models.ForeignKey(User, on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course=models.ForeignKey(Course, on_delete=models.CASCADE)
    title=models.CharField(max_length=255)
    content=models.URLField()
    created_at=models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title


class Student(models.Model):
    course=ManyToManyField(Course)
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Review(models.Model):
    course=models.ForeignKey(Course, on_delete=models.CASCADE)
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    rating=models.IntegerField(validators=[MinValueValidator(1),MaxValueValidator(5)])
    comment=models.CharField(max_length=255, blank=True, null=True)
    created_at=models.DateField(blank=True, null=True)

    def __str__(self):
        return self.user.username

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(auto_now_add=True)

    def str(self):
        return f"{self.user.username} - {self.course.title} - {self.status}"




class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey('Course', related_name='enrollments', on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')


