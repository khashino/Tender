from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from viewflow import jsonstore
from django.utils import timezone
from viewflow.workflow.models import Process

class App1User(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='app1_users',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='app1_users',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    class Meta:
        db_table = 'app1_users'
        verbose_name = 'App1 User'
        verbose_name_plural = 'App1 Users'

    def __str__(self):
        return self.username 
    

class HelloWorldProcess(Process):
    text = jsonstore.CharField(max_length=150)
    approved = jsonstore.BooleanField(default=False)

    class Meta:
        proxy = True