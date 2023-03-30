from .models import *
from django.http import HttpResponseBadRequest
from django.utils.translation import gettext as _

ALL_COURSE_TIMETABLE = [[week, _("%d week" % week)] for week in range(1, 50)]

NAVOICA_SETTINGS_ADDITIONAL_FIELDS = {
    'difficulty':
    {
        'display_name': _("Course Difficulty"),
        'options': list(CourseDifficulty.objects.values_list('id','title')),
        'help': '',
        'sortable': False
    },
    'organizer':
    {
        'display_name': _("Course Organizer"),
        'options': list(CourseOrganizer.objects.values_list('id','title')),
        'help': '',
        'sortable': True
    },
    'course_category':
    {
        'display_name': _("Course Category"),
        'options': list(CourseCategory.objects.values_list('id','title')),
        'help': '',
        'sortable': True
    },
    'timetable':
    {
        'display_name': _("Course Timetable"),
        'options': ALL_COURSE_TIMETABLE,
        'help': '',
        'sortable': False
    },
}
