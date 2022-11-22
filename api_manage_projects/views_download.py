from api_manage_projects.views_generics import GenericViewProject
from api_manage_projects.views_generics import ProjectState
from api_manage_projects.models import user_project_audio_path
from api_manage_projects.models import user_project_midifile_path
from api_manage_projects.models import user_project_midifile_norythm_path
from api_manage_projects.models import user_project_musicxmlfile_path
from django.http import HttpResponse
from rest_framework.response import Response
from api_manage_projects.serializers import PitchResultSerializer
from api_manage_projects.serializers import StepResultSerializer
from rest_framework import status
import math


def ReplaceNaNwithNull(DataList):
    ListOutput = []
    for data in DataList:
        if(math.isnan(data) or math.isinf(data)):
            ListOutput.append(None)
        else:
            ListOutput.append(data)
    return(ListOutput)


class DownloadPitchResultViewProject(GenericViewProject, ProjectState):
    serializer_class = PitchResultSerializer

    def get(self, request, pk):
        instance = self.get_object()
        self.check_projectstate(1, raise_exception=True)
        serializer = self.get_serializer(instance.pitchdetectionresult)
        Response_data = serializer.data
        Response_data['pitch_st'] = ReplaceNaNwithNull(Response_data['pitch_st'])
        Response_data['energy_db'] = ReplaceNaNwithNull(Response_data['energy_db'])
        return Response(Response_data, status=status.HTTP_200_OK)


class DownloadStepResultViewProject(GenericViewProject, ProjectState):
    serializer_class = StepResultSerializer

    def get(self, request, pk):
        instance = self.get_object()
        self.check_projectstate(2, raise_exception=True)
        serializer = self.get_serializer(instance.pitchdetectionresult.stepdetectionresult)
        return Response(serializer.data)


class DownloadAudioViewProject(GenericViewProject, ProjectState):
    def get(self, request, pk):
        instance = self.get_object()
        filepath = user_project_audio_path(instance, None)
        with open(filepath, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="audio/wav")
            response['Content-Disposition'] = 'attachment; filename=audio.wav'
        return(response)


class DownloadMusicXMLViewProject(GenericViewProject, ProjectState):
    def get(self, request, pk):
        instance = self.get_object()
        self.check_projectstate(3)
        instanceresult = instance.pitchdetectionresult.stepdetectionresult.rythmdetectionresult
        filepath = user_project_musicxmlfile_path(instanceresult, None)
        with open(filepath, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/xml")
            response['Content-Disposition'] = 'attachment; filename=score.xml'
        return(response)


class DownloadMidiViewProject(GenericViewProject, ProjectState):
    def get(self, request, pk):
        instance = self.get_object()
        self.check_projectstate(3)
        instanceresult = instance.pitchdetectionresult.stepdetectionresult.rythmdetectionresult
        filepath = user_project_midifile_path(instanceresult, None)
        with open(filepath, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/x-midi")
            response['Content-Disposition'] = 'attachment; filename=score.mid'
        return(response)


class DownloadMidiNorythmViewProject(GenericViewProject, ProjectState):
    def get(self, request, pk):
        instance = self.get_object()
        self.check_projectstate(3)
        instanceresult = instance.pitchdetectionresult.stepdetectionresult.rythmdetectionresult
        filepath = user_project_midifile_norythm_path(instanceresult, None)
        with open(filepath, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/x-midi")
            response['Content-Disposition'] = 'attachment; filename=score_norythm.mid'
        return(response)
