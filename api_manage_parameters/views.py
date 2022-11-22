from rest_framework import generics
from api_manage_users.permissions import IsOwnerOrReadOnly
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from api_manage_parameters.serializers import PitchDetectionParamSerializer
from api_manage_parameters.serializers import StepDetectionParamSerializer
from api_manage_parameters.serializers import RythmDetectionParamSerializer
from api_manage_parameters.serializers import GlobalParamSerializer
from api_manage_parameters.serializers import CreatePitchDetectionParamSerializer
from api_manage_parameters.serializers import CreateStepDetectionParamSerializer
from api_manage_parameters.serializers import CreateRythmDetectionParamSerializer
from api_manage_parameters.serializers import CreateGlobalParamSerializer
from api_manage_parameters.models import PitchDetectionParam
from api_manage_parameters.models import StepDetectionParam
from api_manage_parameters.models import RythmDetectionParam
from api_manage_parameters.models import GlobalParam
from django.db.models.query import QuerySet
from api_manage_parameters.models import DEFAULT_PARAMETER_NAME

from django.conf import settings
from rest_framework.exceptions import ValidationError


class GenericViewParam(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly, )
    parameter_class = None
    serializer_class = None

    def get_queryset(self):
        queryset = self.parameter_class.objects.all()
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        return(queryset)

    def get_owner_queryset(self):
        queryset = self.get_queryset()
        queryset = queryset.filter(owner=self.request.user)
        return(queryset)

    def ParamNameErrors(self, serializer, put_request=False):
        # If name is not one of the modified fields
        if not (serializer.validated_data.__contains__('name')):
            return({})

        NewName = serializer.validated_data.get("name")
        if(put_request):
            OldName = self.get_object().name
            # If the parameter modified is the default one
            if((OldName == DEFAULT_PARAMETER_NAME) and (NewName == DEFAULT_PARAMETER_NAME)):
                return({})
            elif((OldName == DEFAULT_PARAMETER_NAME) and (NewName != DEFAULT_PARAMETER_NAME)):
                response_data = {'name': ["Default parameters cannot be renamed."]}
                return(response_data)

        queryset = self.get_owner_queryset()
        queryset = queryset.filter(name=NewName)
        if(put_request):
            queryset = queryset.exclude(id=self.get_object().id)

        if(queryset.exists()):
            response_data = {'name': ["This parameter name already exists."]}
            return(response_data)

        return({})


class GenericListViewParam(GenericViewParam):

    def check_userexceedparameternumber(self, raise_exception=False):
        queryset_parameter = self.get_owner_queryset()
        NumberOfParametersExceeded = len(queryset_parameter) >= settings.MAX_PARAMETER_NUMBER
        if(NumberOfParametersExceeded and raise_exception):
            response_data = {'parameter': ["The number of parameters is exceeded"]}
            raise ValidationError(response_data)
        return(NumberOfParametersExceeded)

    def get(self, request):
        queryset = self.filter_queryset(self.get_owner_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        self.check_userexceedparameternumber(raise_exception=True)
        serializer.is_valid(raise_exception=True)
        response_data = self.ParamNameErrors(serializer)
        if(response_data != {}):
            return(Response(response_data, status=status.HTTP_400_BAD_REQUEST))
        serializer.save(owner=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GenericDetailsViewParam(GenericViewParam):

    def check_IsNotDefaultParameter(self, raise_exception=False):
        instance = self.get_object()
        IsDefaultParam = instance.name == DEFAULT_PARAMETER_NAME
        if(raise_exception and IsDefaultParam):
            response_data = {'name': ["Cannot modify/delete defaults parameters"]}
            raise ValidationError(response_data)
        return(IsDefaultParam)

    def get(self, request, pk):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def delete(self, request, pk):
        instance = self.get_object()
        self.check_IsNotDefaultParameter(raise_exception=True)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk):
        self.check_IsNotDefaultParameter(raise_exception=True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        response_data = self.ParamNameErrors(serializer, put_request=True)
        if(response_data != {}):
            return(Response(response_data, status=status.HTTP_400_BAD_REQUEST))
        serializer.save()
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)


class GenericGlobalViewParam():

    def ParamNamePitchDetectionExists(self, serializer):
        if not (serializer.validated_data.__contains__('namepitchdetectionparam')):
            return(True)
        queryset = self.parameter_pitch_class.objects.all()
        queryset = queryset.filter(owner=self.request.user, name=serializer.validated_data.get("namepitchdetectionparam"))
        return(queryset.exists())

    def ParamNameStepDetectionExists(self, serializer):
        if not (serializer.validated_data.__contains__('namestepdetectionparam')):
            return(True)
        queryset = self.parameter_step_class.objects.all()
        queryset = queryset.filter(owner=self.request.user, name=serializer.validated_data.get("namestepdetectionparam"))
        return(queryset.exists())

    def ParamNameRythmDetectionExists(self, serializer):
        if not (serializer.validated_data.__contains__('namerythmdetectionparam')):
            return(True)
        queryset = self.parameter_rythm_class.objects.all()
        queryset = queryset.filter(owner=self.request.user, name=serializer.validated_data.get("namerythmdetectionparam"))
        return(queryset.exists())


# PitchDetectionParam
class ListViewPitchDetectionParam(GenericListViewParam):
    serializer_class = CreatePitchDetectionParamSerializer
    parameter_class = PitchDetectionParam


class DetailsViewPitchDetectionParam(GenericDetailsViewParam):
    serializer_class = PitchDetectionParamSerializer
    parameter_class = PitchDetectionParam


# StepDetectionParam
class ListViewStepDetectionParam(GenericListViewParam):
    serializer_class = CreateStepDetectionParamSerializer
    parameter_class = StepDetectionParam


class DetailsViewStepDetectionParam(GenericDetailsViewParam):
    serializer_class = StepDetectionParamSerializer
    parameter_class = StepDetectionParam


# RythmDetectionParam
class ListViewRythmDetectionParam(GenericListViewParam):
    serializer_class = CreateRythmDetectionParamSerializer
    parameter_class = RythmDetectionParam


class DetailsViewRythmDetectionParam(GenericDetailsViewParam):
    serializer_class = RythmDetectionParamSerializer
    parameter_class = RythmDetectionParam


# GlobalParam
class ListViewGlobalParam(GenericListViewParam, GenericGlobalViewParam):
    serializer_class = CreateGlobalParamSerializer
    parameter_class = GlobalParam
    parameter_pitch_class = PitchDetectionParam
    parameter_step_class = StepDetectionParam
    parameter_rythm_class = RythmDetectionParam

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        self.check_userexceedparameternumber(raise_exception=True)
        serializer.is_valid(raise_exception=True)
        response_data = self.ParamNameErrors(serializer)
        if not (self.ParamNamePitchDetectionExists(serializer)):
            response_data['namepitchdetectionparam'] = ["This parameter name doesn't exists."]
        if not (self.ParamNameStepDetectionExists(serializer)):
            response_data['namestepdetectionparam'] = ["This parameter name doesn't exists."]
        if not (self.ParamNameRythmDetectionExists(serializer)):
            response_data['namerythmdetectionparam'] = ["This parameter name doesn't exists."]
        if(response_data != {}):
            return(Response(response_data, status=status.HTTP_400_BAD_REQUEST))
        serializer.save(owner=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DetailsViewGlobalParam(GenericDetailsViewParam, GenericGlobalViewParam):
    serializer_class = GlobalParamSerializer
    parameter_class = GlobalParam
    parameter_pitch_class = PitchDetectionParam
    parameter_step_class = StepDetectionParam
    parameter_rythm_class = RythmDetectionParam

    def put(self, request, pk):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        response_data = self.ParamNameErrors(serializer, put_request=True)
        if not (self.ParamNamePitchDetectionExists(serializer)):
            response_data['namepitchdetectionparam'] = ["This parameter name doesn't exists."]
        if not (self.ParamNameStepDetectionExists(serializer)):
            response_data['namestepdetectionparam'] = ["This parameter name doesn't exists."]
        if not (self.ParamNameRythmDetectionExists(serializer)):
            response_data['namerythmdetectionparam'] = ["This parameter name doesn't exists."]
        if(response_data != {}):
            return(Response(response_data, status=status.HTTP_400_BAD_REQUEST))
        serializer.save()
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)
