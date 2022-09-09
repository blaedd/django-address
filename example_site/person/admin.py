from django.contrib import admin

from address.forms import AddressWidget
from address.models import AddressField
from .models import Person


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "first_name",
        "address",
    )

    formfield_overrides = {AddressField: {"widget": AddressWidget(attrs={"style": "width: 300px;"})}}
