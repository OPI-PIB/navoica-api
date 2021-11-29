import copy
from datetime import datetime, timedelta

import simplejson
from cms.djangoapps.models.settings.course_metadata import CourseMetadata
from django.contrib.auth.models import AnonymousUser
from django.core.management.base import BaseCommand
from django.utils.encoding import force_text
from django.utils.functional import Promise
from openedx.core.djangoapps.content.course_overviews.models import \
    CourseOverview
from pytz import utc
from six import text_type
from xmodule.modulestore.django import modulestore


class ExtendedJSONEncoder(simplejson.JSONEncoder):
    def default(self, o):  # pylint: disable=method-hidden
        if isinstance(o, Promise):
            return force_text(o)
        else:
            return super(ExtendedJSONEncoder, self).default(o)


class Command(BaseCommand):
    help = 'Refresh availability for course discovery'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.now = datetime.now(utc)
        self.upcoming_cutoff = self.now + timedelta(days=60)
        self.stdout.write(self.style.SUCCESS('I am starting ...'))
        self.stdout.write(self.style.SUCCESS('. means next course'))

    def handle(self, *args, **options):
        for course in modulestore().get_courses():
            self.stdout.write(self.style.SUCCESS('.'))
            course_id = text_type(course.id)
            course_metadata = CourseMetadata.fetch_all(course)
            course_metadata_copy = copy.deepcopy(course_metadata)
            course_overview_model = CourseOverview.get_from_id(course_id=course_id)
            update_flag = False
            if course_overview_model:
                availability_status = self.get_availability(course_overview_model.start_date, course_overview_model.end_date)
                if not(course_metadata_copy['other_course_settings']['value'].get('availability')
                       and course_metadata_copy['other_course_settings']['value'].get('availability') == availability_status):
                    if availability_status:
                        course_metadata_copy['other_course_settings']['value']['availability'] = availability_status
                        update_flag = True
                    else:
                        if course_metadata_copy['other_course_settings']['value'].get('availability'):
                            del course_metadata_copy['other_course_settings']['value']['availability']
                            update_flag = True
                    if update_flag:
                        other_course_settings_dict = simplejson.loads(simplejson.dumps(
                            {'other_course_settings': course_metadata_copy['other_course_settings']}, cls=ExtendedJSONEncoder))
                        CourseMetadata.update_from_json(course, other_course_settings_dict, AnonymousUser())

        self.stdout.write(self.style.SUCCESS('Successfully finished'))

    def get_availability(self, start_date, end_date):
        if (start_date and end_date):
            if (end_date and (end_date < self.now)):
                return 'archived'
            elif (start_date and (start_date <= self.now)):
                return 'in_progress'
            elif (start_date and (self.now < start_date < self.upcoming_cutoff)):
                return 'starting_soon'
            else:
                return 'upcoming'
        else:
            return False
