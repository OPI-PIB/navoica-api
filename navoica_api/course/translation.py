from modeltranslation.translator import translator, TranslationOptions
from .models import *

class CourseOrganizerTranslationOptions(TranslationOptions):
    fields = ('title', 'image')

translator.register(CourseOrganizer, CourseOrganizerTranslationOptions)

class CourseTitleTranslationOptions(TranslationOptions):
    fields = ('title',)

translator.register(CourseDifficulty, CourseTitleTranslationOptions)
translator.register(CourseCategory, CourseTitleTranslationOptions)