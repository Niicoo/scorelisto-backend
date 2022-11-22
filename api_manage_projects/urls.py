from django.urls import re_path
from rest_framework.urlpatterns import format_suffix_patterns

from api_manage_projects.views_base import ListViewProject
from api_manage_projects.views_base import DetailsViewProject

from api_manage_projects.views_convertion import PitchDetectionProject
from api_manage_projects.views_convertion import StepDetectionProject
from api_manage_projects.views_convertion import RythmDetectionProject
from api_manage_projects.views_convertion import DirectConversionProject
from api_manage_projects.views_convertion import FreeConversion

from api_manage_projects.views_download import DownloadPitchResultViewProject
from api_manage_projects.views_download import DownloadStepResultViewProject

from api_manage_projects.views_download import DownloadAudioViewProject
from api_manage_projects.views_download import DownloadMusicXMLViewProject
from api_manage_projects.views_download import DownloadMidiViewProject
from api_manage_projects.views_download import DownloadMidiNorythmViewProject

from api_manage_projects.views_task import CheckTasksState
from api_manage_projects.views_task import RevokeTask


uuid_regex = r'([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}){1}'

urlpatterns = {
    re_path(r'^project\/freeconversion\/?$', FreeConversion.as_view(), name="free_conversion"),
    re_path(r'^project\/?$', ListViewProject.as_view(), name="create_project"),
    re_path(r'^project\/(?P<pk>\d{1,10})\/?$', DetailsViewProject.as_view(), name="details_project"),
    re_path(r'^project\/(?P<pk>\d{1,10})\/download\/pitch\/?$', DownloadPitchResultViewProject.as_view(), name="download_project_pitch"),
    re_path(r'^project\/(?P<pk>\d{1,10})\/download\/step\/?$', DownloadStepResultViewProject.as_view(), name="download_project_step"),
    re_path(r'^project\/(?P<pk>\d{1,10})\/download\/audio\/?$', DownloadAudioViewProject.as_view(), name="download_project_audio"),
    re_path(r'^project\/(?P<pk>\d{1,10})\/download\/musicxml\/?$', DownloadMusicXMLViewProject.as_view(), name="download_project_musicxml"),
    re_path(r'^project\/(?P<pk>\d{1,10})\/download\/midi\/?$', DownloadMidiViewProject.as_view(), name="download_project_midi"),
    re_path(r'^project\/(?P<pk>\d{1,10})\/download\/midinorythm\/?$', DownloadMidiNorythmViewProject.as_view(), name="download_project_midinorythm"),
    re_path(r'^project\/(?P<pk>\d{1,10})\/runpitchdetection\/?$', PitchDetectionProject.as_view(), name="pitchdetection_project"),
    re_path(r'^project\/(?P<pk>\d{1,10})\/runstepdetection\/?$', StepDetectionProject.as_view(), name="stepdetection_project"),
    re_path(r'^project\/(?P<pk>\d{1,10})\/runrythmdetection\/?$', RythmDetectionProject.as_view(), name="rythmdetection_project"),
    re_path(r'^project\/(?P<pk>\d{1,10})\/rundirectconversion\/?$', DirectConversionProject.as_view(), name="directconversion_project"),
    re_path(r'^project\/task\/checkstate\/?$', CheckTasksState.as_view(), name="checktask_project"),
    re_path(r'^project\/task\/revoke\/(?P<task_id>' + uuid_regex + r')\/?$', RevokeTask.as_view(), name="revoketask_project"),
}

urlpatterns = format_suffix_patterns(urlpatterns)
