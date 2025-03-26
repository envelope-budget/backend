from django.contrib import admin

from .models import Category, Envelope


class EnvelopeAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["name", "budget", "category"]

    def get_queryset(self, request):
        return Envelope.objects.include_all()


admin.site.register(Envelope, EnvelopeAdmin)


class CategoryAdmin(admin.ModelAdmin):
    pass


admin.site.register(Category, CategoryAdmin)
