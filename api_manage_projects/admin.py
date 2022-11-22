from django.contrib import admin
from api_manage_projects.models import Project

from api_manage_projects.models import PitchDetectionResult
from api_manage_projects.models import StepDetectionResult
from api_manage_projects.models import RythmDetectionResult
from api_manage_projects.models import ProjectPitchDetectionParam
from api_manage_projects.models import ProjectStepDetectionParam
from api_manage_projects.models import ProjectRythmDetectionParam

from api_manage_projects.models import ProjectProcess

admin.site.register(PitchDetectionResult)
admin.site.register(StepDetectionResult)
admin.site.register(RythmDetectionResult)
admin.site.register(ProjectPitchDetectionParam)
admin.site.register(ProjectStepDetectionParam)
admin.site.register(ProjectRythmDetectionParam)
admin.site.register(ProjectProcess)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'audiofile', )


admin.site.register(Project, ProjectAdmin)
