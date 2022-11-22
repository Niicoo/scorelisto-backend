from api_manage_users.permissions import IsOwnerOrReadOnly
from django.db.models.query import QuerySet

from django.conf import settings
from rest_framework import generics
from rest_framework import permissions
from rest_framework.exceptions import ValidationError

from api_manage_projects.models import Project
from api_manage_projects.models import ProjectProcess


class GenericViewProject(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly,)
    serializer_class = None

    def get_queryset(self):
        queryset = Project.objects.all()
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        return(queryset)

    def get_user(self):
        return(self.request.user)

    def get_owner_queryset(self):
        queryset = self.get_queryset()
        queryset = queryset.filter(owner=self.request.user)
        return(queryset)

    def ProjectNameAlreadyExists(self, serializer, put_request=False):
        # If name is not one of the modified fields
        if not ('name' in list(serializer.validated_data.keys())):
            return(False)
        NewName = serializer.validated_data.get("name")
        queryset = self.get_owner_queryset()
        queryset = queryset.filter(name=NewName)
        if(put_request):
            queryset = queryset.exclude(id=self.get_object().id)
        if(queryset.exists()):
            return(True)
        return(False)


class ProjectState():
    def check_projectstate(self, statemin, raise_exception=False):
        project_instance = self.get_object()
        projectstate = project_instance.get_projectstate()
        IsStateOk = projectstate >= statemin
        if((IsStateOk is False) and raise_exception):
            response_data = {'projectstate': ["you need to proceed to previous steps processing this step"]}
            raise ValidationError(response_data)
        return(IsStateOk)

    def check_processalreadyrunning(self, raise_exception=False):
        project_instance = self.get_object()
        WIP = project_instance.is_processrunning()
        if(raise_exception and WIP):
            response_data = {'project': ["A process is already running for this project"]}
            raise ValidationError(response_data)
        return(WIP)

    def check_userexceedprocessnumber(self, raise_exception=False):
        project_instance = self.get_object()
        queryset_projectprocess = ProjectProcess.objects.filter(owner=project_instance.owner)
        NumberOfProcessExceeded = len(queryset_projectprocess) >= settings.MAX_PROCESS_NUMBER
        if(NumberOfProcessExceeded and raise_exception):
            response_data = {'project': ["The number of running process is exceeded, please wait"]}
            raise ValidationError(response_data)
        return(NumberOfProcessExceeded)
