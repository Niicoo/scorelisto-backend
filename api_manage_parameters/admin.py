from django.contrib import admin
from api_manage_parameters.models import PitchDetectionParam
from api_manage_parameters.models import StepDetectionParam
from api_manage_parameters.models import RythmDetectionParam
from api_manage_parameters.models import GlobalParam


class PitchDetectionParamAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', )


class StepDetectionParamAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', )


class RythmDetectionParamAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', )


class GlobalParamAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', )


admin.site.register(PitchDetectionParam, PitchDetectionParamAdmin)
admin.site.register(StepDetectionParam, StepDetectionParamAdmin)
admin.site.register(RythmDetectionParam, RythmDetectionParamAdmin)
admin.site.register(GlobalParam, GlobalParamAdmin)
