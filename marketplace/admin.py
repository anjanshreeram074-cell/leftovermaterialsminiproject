from django.contrib import admin
from .models import User, Material, MaterialImage, Location

admin.site.register(User)
admin.site.register(Material)
admin.site.register(MaterialImage)
admin.site.register(Location)
