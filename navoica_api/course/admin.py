from django.contrib import admin
from .models import *
from modeltranslation.admin import TranslationAdmin

class CourseOrganizerAdmin(TranslationAdmin):

    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields if "_" in  field.name]
        super(CourseOrganizerAdmin, self).__init__(model, admin_site)

    def has_delete_permission(self, request, obj=None):
        return False

    readonly_fields = ['id',]

admin.site.register(CourseOrganizer, CourseOrganizerAdmin)
admin.site.register(CourseDifficulty, CourseOrganizerAdmin)
admin.site.register(CourseCategory, CourseOrganizerAdmin)