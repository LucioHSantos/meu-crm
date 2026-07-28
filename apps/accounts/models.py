from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('salesperson', 'Salesperson'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='salesperson')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.get_full_name() or self.username

    def is_admin_user(self):
        return self.role == 'admin'

    def is_manager(self):
        return self.role == 'manager'

    def is_salesperson(self):
        return self.role == 'salesperson'
