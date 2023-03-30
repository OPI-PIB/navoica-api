from django.utils import translation
from django.db import migrations, models
from django.utils.translation import ugettext
from django.core.files import File
from os.path import exists
from django.template.defaultfilters import slugify


def get_translation_in(string, locale):
    translation.activate(locale)
    val = ugettext(string)
    translation.deactivate()
    return val


ALL_COURSE_DIFFICULTY = [
    ["easy", "introductory"],
    ["medium", "intermediate"],
    ["hard", "advanced"]
]

ALL_COURSE_ORGANIZER = [
    ["1", "Young Science Foundation"],
    ["2", "Warsaw University of Technology"],
    ["3", "Lodz University of Technology"],
    ["4", "National Information Processing Institute"],
    ["5", "Helena Chodkowska University of Technology and Economics"],
    ["6", "Vistula University "],
    ["7", "Akademia Ignatianum w Krakowie"],
    ["8", "War Studies University"],
    ["9", "WSB University"],
    ["10", "The Witelon State University of Applied Sciences in Legnica"],
    ["11", "Bialystok University of Technology"],
    ["12", "Czestochowa University of Technology"],
    ["13", "Gdansk University of Technology"],
    ["14", "Cracow University of Technology"],
    ["15", "Public Univerity of Humanities ‘POMERANIA’"],
    ["16", "Paweł Włodkowic University College in Płock"],
    ["17", "Poznań University of Economics and Business "],
    ["18", "Jan Długosz University in Częstochowa "],
    ["19", "Adam Mickiewicz University in Poznań"],
    ["20", "Jagiellonian University in Kraków"],
    ["21", "Cardinal Wyszyński University in Warsaw"],
    ["22", "Nicolaus Copernicus University in Toruń"],
    ["23", "Pedagogical University of Krakow"],
    ["24", "Uniwersytet Szczeciński"],
    ["25", "University of Silesia in Katowice"],
    ["26", "UTP University of Science and Technology"],
    ["27", "Kazimierz Pułaski University of Technology and Humanities in Radom"],
    ["28", "Military University of Technology"],
    ["29", "College of Business and Entrepreneurship in Ostrowiec Świętokrzyski"],
    ["30", "Lipinski University"],
    ["31", "University of Economy in Bydgoszcz"],
    ["32", "University of Business in Wrocław"],
    ["33", "TWP Higher School of Humanities"],
    ["34", "Humanitas University in Sosnowiec"],
    ["35", "The University of Information Technology and Management in Rzeszów"],
    ["36", "Academy of European Integration in Szczecin"],
    ["37", "WSPiA University of Rzeszow"],
    ["38", "Katowice School of Technology"],
    ["39", "West Pomeranian Business School"],
    ["40", "West Pomeranian University of Technology in Szczecin"],
    ["41", "Copernicus Science Centre"],
    ["42", "Pomeranian University in Słupsk"],
    ["43", "Collegium Humanum – Warsaw Management University"],
    ["44", "Parlament Studentów Rzeczypospolitej Polskiej"],
    ["45", "The Warsaw Institute of Banking"],
    ["46", "University of Economics and Human Sciences in Warsaw"],
    ["47", "Skills Council for the Chemical Sector"],
    ["48", "University of Technology and Life Sciences in Bydgoszcz"],
    ["49", "Witelon Collegium State University"],
    ["50", "Maria Curie-Skłodowska University"],
    ["51", "Akademia Nauk Stosowanych im. Józefa Gołuchowskiego"],
    ["52", "Wroclaw Business University"],
    ["53", "HumanDoc Foundation"]
]

ALL_COURSE_CATEGORY = [
    ["agricultural", "Agriculture"],
    ["art", "Arts"],
    ["biology", "Biology"],
    ["management", "Business and Management"],
    ["chemical", "Chemistry"],
    ["computer", "Computer Science"],
    ["ecology", "Ecology"],
    ["business", "Economics and Finance"],
    ["education", "Education"],
    ["technical", "Engineering"],
    ["geography", "Geography"],
    ["health", "Health"],
    ["human", "Humanities"],
    ["language", "Language learning"],
    ["laws", "Law"],
    ["math", "Mathematics"],
    ["medicine", "Medicine"],
    ["natural", "Nature and Environment"],
    ["pedagogy", "Pedagogy and Didactics"],
    ["selfdevelopment", "Personal development"],
    ["physics", "Physics"],
    ["politics", "Politics"],
    ["programming", "Programming"],
    ["psychology", "Psychology"],
    ["social", "Sociology"],
    ["system", "Systems for science and higher education"],
]


def migrate_data(apps, schema_editor):
    CourseOrganizer = apps.get_model('navoica_course', 'CourseOrganizer')
    CourseDifficulty = apps.get_model('navoica_course', 'CourseDifficulty')
    CourseCategory = apps.get_model('navoica_course', 'CourseCategory')

    for org in ALL_COURSE_ORGANIZER:
        id = org[0]
        title_en = org[1]
        title_pl = get_translation_in(title_en, 'pl')

        path = "/edx/app/edxapp/edx-platform/themes/navoica-theme/lms/static/images/org/" + \
            get_translation_in(title_en, 'pl')+".png"

        co = CourseOrganizer.objects.create(
            id=id, title_pl=title_pl, title_en=title_en)
        if exists(path):
            co.image_pl = File(file=open(path, 'rb'),
                               name=slugify(title_en)+'.png')
            co.save()

    for diff in ALL_COURSE_DIFFICULTY:
        id = diff[0]
        title_en = diff[1]
        title_pl = get_translation_in(title_en, 'pl')
        CourseDifficulty.objects.create(id=id, title_pl=title_pl, title_en=title_en)

    for cat in ALL_COURSE_CATEGORY:
        id = cat[0]
        title_en = cat[1]
        title_pl = get_translation_in(title_en, 'pl')
        CourseCategory.objects.create(id=id, title_pl=title_pl, title_en=title_en)

class Migration(migrations.Migration):

    dependencies = [
        ('navoica_course', '0004_auto_20230328_1020'),
    ]

    operations = [
        migrations.RunPython(migrate_data)
    ]
