"""Back end set up for Events."""
from django.contrib import admin

from talesofvalor.skills.models import Header, Skill


class HeaderAdmin(admin.ModelAdmin):
    """Access the Header from the admin."""

    pass


class SkillAdmin(admin.ModelAdmin):
    """Access the Skill from the admin."""

    pass

# Register the admin models
admin.site.register(Header, HeaderAdmin)
admin.site.register(Skill, SkillAdmin)