from django.contrib import admin

from .models import Category, Envelope


class EnvelopeAdmin(admin.ModelAdmin):
    pass


admin.site.register(Envelope, EnvelopeAdmin)


class CategoryAdmin(admin.ModelAdmin):
    pass


admin.site.register(Category, CategoryAdmin)
