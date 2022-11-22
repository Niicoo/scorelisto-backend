from django.urls import re_path
from rest_framework.urlpatterns import format_suffix_patterns

from api_manage_parameters.views import ListViewPitchDetectionParam
from api_manage_parameters.views import DetailsViewPitchDetectionParam

from api_manage_parameters.views import ListViewStepDetectionParam
from api_manage_parameters.views import DetailsViewStepDetectionParam

from api_manage_parameters.views import ListViewRythmDetectionParam
from api_manage_parameters.views import DetailsViewRythmDetectionParam

from api_manage_parameters.views import ListViewGlobalParam
from api_manage_parameters.views import DetailsViewGlobalParam


urlpatterns = {
    re_path(r'^parameter\/pitchdetection\/?$', ListViewPitchDetectionParam.as_view(), name="create_pitchdetectionparam"),
    re_path(r'^parameter\/pitchdetection\/(?P<pk>\d{1,10})\/?$', DetailsViewPitchDetectionParam.as_view(), name="details_pitchdetectionparam"),
    re_path(r'^parameter\/stepdetection\/?$', ListViewStepDetectionParam.as_view(), name="create_stepdetectionparam"),
    re_path(r'^parameter\/stepdetection\/(?P<pk>\d{1,10})\/?$', DetailsViewStepDetectionParam.as_view(), name="details_stepdetectionparam"),
    re_path(r'^parameter\/rythmdetection\/?$', ListViewRythmDetectionParam.as_view(), name="create_rythmdetectionparam"),
    re_path(r'^parameter\/rythmdetection\/(?P<pk>\d{1,10})\/?$', DetailsViewRythmDetectionParam.as_view(), name="details_rythmdetectionparam"),
    re_path(r'^parameter\/global\/?$', ListViewGlobalParam.as_view(), name="create_globalparam"),
    re_path(r'^parameter\/global\/(?P<pk>\d{1,10})\/?$', DetailsViewGlobalParam.as_view(), name="details_globalparam")
}

urlpatterns = format_suffix_patterns(urlpatterns)
