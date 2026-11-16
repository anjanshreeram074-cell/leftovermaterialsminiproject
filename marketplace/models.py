from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    phone = models.CharField(max_length=15, blank=True)

class Material(models.Model):
    CATEGORY_CHOICES = (
        ('tiles', 'Tiles'),
        ('cement', 'Cement'),
        ('bricks', 'Bricks'),
        ('steel', 'Steel'),
        ('pipes', 'Pipes'),
        ('other', 'Other'),
    )
    CONDITION_CHOICES = (
        ('unused', 'Unused'),
        ('opened', 'Opened'),
        ('used', 'Used'),
    )
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('sold', 'Sold'),
    )

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['category', 'status']),
        ]

class MaterialImage(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField()
    position = models.IntegerField()

class Location(models.Model):
    owner_type = models.CharField(max_length=20) # 'user' or 'material'
    owner_id = models.IntegerField()
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=['lat', 'lng']),
        ]

class DistanceCache(models.Model):
    origin_lat = models.DecimalField(max_digits=9, decimal_places=6)
    origin_lng = models.DecimalField(max_digits=9, decimal_places=6)
    dest_lat = models.DecimalField(max_digits=9, decimal_places=6)
    dest_lng = models.DecimalField(max_digits=9, decimal_places=6)
    km = models.DecimalField(max_digits=10, decimal_places=2)
    minutes = models.IntegerField()
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=['origin_lat', 'origin_lng', 'dest_lat', 'dest_lng']),
            models.Index(fields=['expires_at']),
        ]
