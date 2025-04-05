from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class App2User(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='app2_users',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='app2_users',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    class Meta:
        db_table = 'app2_users'
        verbose_name = 'App2 User'
        verbose_name_plural = 'App2 Users'

    def __str__(self):
        return self.username 