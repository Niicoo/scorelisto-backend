from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from api_manage_projects.views_generics import GenericViewProject

from api_manage_projects.serializers import CreateProjectSerializer
from api_manage_projects.serializers import ProjectSerializer

import wave

from django.conf import settings


def AddProjectStateAndTaskId(project_instance, serializer_data):
    projectstate = project_instance.get_projectstate()
    serializer_data['state'] = projectstate
    if(project_instance.is_processrunning()):
        serializer_data['task_id'] = project_instance.projectprocess.task_id
        serializer_data['task_name'] = project_instance.projectprocess.task_name
    else:
        serializer_data['task_id'] = ''
        serializer_data['task_name'] = ''
    return(serializer_data)


class ListViewProject(GenericViewProject):
    serializer_class = CreateProjectSerializer

    def check_userexceedmemory(self, NewFileSize, raise_exception=False):
        user = self.get_user()
        FreeMemory = user.profile.get_user_memory_remaining()
        MemoryExceeded = NewFileSize > FreeMemory
        if(MemoryExceeded and raise_exception):
            response_data = {'project': ["Maximum memory reached"]}
            raise ValidationError(response_data)
        return(MemoryExceeded)

    def check_userexceedprojectnumber(self, raise_exception=False):
        queryset_projects = self.get_owner_queryset()
        NumberOfProjectsExceeded = len(queryset_projects) >= settings.MAX_PROJECT_NUMBER
        if(NumberOfProjectsExceeded and raise_exception):
            response_data = {'project': ["The number of projects is exceeded"]}
            raise ValidationError(response_data)
        return(NumberOfProjectsExceeded)

    def check_file(self, file, raise_exception=False):
        try:
            with wave.open(file, mode='r') as wavefile:
                Fe_hz = wavefile.getframerate()
                NbSamples = wavefile.getnframes()
                Length_s = NbSamples / Fe_hz
                if(self.request.user.profile.is_premium):
                    MaxLength = settings.PREMIUM_MAX_LENGTH_TRACK
                else:
                    MaxLength = settings.FREE_MAX_LENGTH_TRACK
                LengthExceeded = Length_s > MaxLength
        except:
            if(raise_exception):
                response_data = {'audio': ["Invalid audio format"]}
                raise ValidationError(response_data)
            return(False)

        if(LengthExceeded and raise_exception):
            response_data = {'audio': ["The length of the audio exceeded the maximum length"]}
            raise ValidationError(response_data)
        return(LengthExceeded)

    def check_projectsperdayexceeded(self, raise_exception=False):
        user_instance = self.request.user
        NumberOfProjectsPerDayExceeded = user_instance.profile.projects_remaining <= 0
        if(NumberOfProjectsPerDayExceeded and raise_exception):
            response_data = {'project': ["Number of project creation per day exceeded"]}
            raise ValidationError(response_data)
        return(NumberOfProjectsPerDayExceeded)

    def get(self, request):
        queryset = self.filter_queryset(self.get_owner_queryset())
        ListProjects = []
        for project in queryset:
            ProjectData = self.get_serializer(project).data
            AddProjectStateAndTaskId(project, ProjectData)
            ListProjects.append(ProjectData)
        return Response(ListProjects)

    def post(self, request):
        # Check that the number of projects is not exceeded
        self.check_userexceedprojectnumber(raise_exception=True)
        # Get the input data
        serializer = self.get_serializer(data=request.data)
        # Check that the serializer is Ok
        serializer.is_valid(raise_exception=True)
        # Check that the user has enought remained memory
        audiofilesize = serializer.validated_data['audiofile'].size
        self.check_userexceedmemory(audiofilesize, raise_exception=True)
        # Check if the input file is correct
        file = serializer.validated_data['audiofile'].file
        self.check_file(file, raise_exception=True)
        # Check that the number of project created per day is not over the limitation
        self.check_projectsperdayexceeded(raise_exception=True)
        # Check the project name does not already exists
        if(self.ProjectNameAlreadyExists(serializer)):
            response_data = {'name': ["This parameter name already exists."]}
            return(Response(response_data, status=status.HTTP_400_BAD_REQUEST))
        project_instance = serializer.save(owner=self.request.user)
        Response_data = serializer.data
        AddProjectStateAndTaskId(project_instance, Response_data)
        return Response(Response_data, status=status.HTTP_201_CREATED)


class DetailsViewProject(GenericViewProject):
    serializer_class = ProjectSerializer

    def get(self, request, pk):
        instance = self.get_object()
        ProjectData = self.get_serializer(instance).data
        projectstate = instance.get_projectstate()
        ProjectData['state'] = projectstate
        if(instance.is_processrunning()):
            ProjectData['task_id'] = instance.projectprocess.task_id
        else:
            ProjectData['task_id'] = ''
        return Response(ProjectData)

    def delete(self, request, pk):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        if(self.ProjectNameAlreadyExists(serializer, put_request=True)):
            response_data = {'name': ["This parameter name already exists."]}
            return(Response(response_data, status=status.HTTP_400_BAD_REQUEST))
        serializer.save()
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        Response_data = serializer.data
        AddProjectStateAndTaskId(instance, Response_data)
        return Response(Response_data)
