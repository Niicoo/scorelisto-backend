import os
import uuid
import errno
import wave
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.exceptions import ValidationError
from rest_framework import generics

from api_manage_projects.views_generics import GenericViewProject
from api_manage_projects.views_generics import ProjectState

from api_manage_projects.serializers import PitchDetectionSerializer
from api_manage_projects.serializers import StepDetectionSerializer
from api_manage_projects.serializers import RythmDetectionSerializer
from api_manage_projects.serializers import DirectConversionSerializer
from api_manage_projects.serializers import FreeConversionSerializer

from api_manage_projects.tasks import runpitchdetection
from api_manage_projects.tasks import runstepdetection
from api_manage_projects.tasks import runrythmdetection
from api_manage_projects.tasks import rundirectconversion
from api_manage_projects.tasks import runfreeconversion

from api_manage_parameters.models import PitchDetectionParam
from api_manage_parameters.models import StepDetectionParam
from api_manage_parameters.models import RythmDetectionParam
from api_manage_parameters.models import GlobalParam

from api_manage_projects.models import ProjectProcess


class PitchDetectionProject(GenericViewProject, ProjectState):
    serializer_class = PitchDetectionSerializer

    def post(self, request, pk):
        # To check if the project id exists
        project_instance = self.get_object()
        # Check if the number of process for this user is exceed
        self.check_userexceedprocessnumber(raise_exception=True)
        # Check if a process is already running for this project
        self.check_processalreadyrunning(raise_exception=True)
        # Check if the parameters are ok
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Delete past results if exists
        if(hasattr(project_instance, "pitchdetectionresult")):
            project_instance.pitchdetectionresult.delete()
        # If parameters are ok:
        if(serializer.validated_data.__contains__('timestart_s')):
            timestart_s = serializer.validated_data.get('timestart_s')
        else:
            timestart_s = None
        if(serializer.validated_data.__contains__('timestop_s')):
            timestop_s = serializer.validated_data.get('timestop_s')
        else:
            timestop_s = None
        task = runpitchdetection.delay(project_instance.id, serializer.validated_data, timestart_s, timestop_s)
        ProjectProcess.objects.create(owner=project_instance.owner,
                                      project=project_instance,
                                      task_name="pitch",
                                      task_id=task.id)
        return Response({'task_id': task.id}, status=status.HTTP_201_CREATED)


class StepDetectionProject(GenericViewProject, ProjectState):
    serializer_class = StepDetectionSerializer

    def post(self, request, pk):
        # To check if the project id exists
        project_instance = self.get_object()
        # Check if the number of process for this user is exceed
        self.check_userexceedprocessnumber(raise_exception=True)
        # Check if a process is already running for this project
        self.check_processalreadyrunning(raise_exception=True)
        # Check if the parameters are ok
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Check if the previous step is done
        self.check_projectstate(1, raise_exception=True)
        # Delete past results if exists
        pitchresult_instance = project_instance.pitchdetectionresult
        if(hasattr(pitchresult_instance, "stepdetectionresult")):
            pitchresult_instance.stepdetectionresult.delete()
        # Run the conversion
        task = runstepdetection.delay(project_instance.id, serializer.validated_data)
        ProjectProcess.objects.create(owner=project_instance.owner,
                                      project=project_instance,
                                      task_name="step",
                                      task_id=task.id)
        return Response({'task_id': task.id}, status=status.HTTP_201_CREATED)


class RythmDetectionProject(GenericViewProject, ProjectState):
    serializer_class = RythmDetectionSerializer

    def post(self, request, pk):
        # Check if the project id exists
        project_instance = self.get_object()
        # Check if the number of process for this user is exceed
        self.check_userexceedprocessnumber(raise_exception=True)
        # Check if a process is already running for this project
        self.check_processalreadyrunning(raise_exception=True)
        # Check if the parameters are ok
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Check if the previous step is done
        self.check_projectstate(2, raise_exception=True)
        # Delete past results if exists
        pitchresult_instance = project_instance.pitchdetectionresult
        stepresult_instance = pitchresult_instance.stepdetectionresult
        if(hasattr(stepresult_instance, "rythmdetectionresult")):
            stepresult_instance.rythmdetectionresult.delete()
        # Run the conversion
        task = runrythmdetection.delay(project_instance.id, serializer.validated_data)
        ProjectProcess.objects.create(owner=project_instance.owner,
                                      project=project_instance,
                                      task_name="rythm",
                                      task_id=task.id)
        return Response({'task_id': task.id}, status=status.HTTP_201_CREATED)


class DirectConversionProject(GenericViewProject, ProjectState):
    serializer_class = DirectConversionSerializer

    def get_globalparam_instance(self, name):
        queryset = GlobalParam.objects.all()
        queryset = queryset.filter(owner=self.request.user, name=name)
        if not queryset.exists():
            response_data = {'nameglobalparam': ["This parameter name does not exists"]}
            raise ValidationError(response_data)
        return(queryset.first())

    def get_pitchdetectionparam_instance(self, name):
        queryset = PitchDetectionParam.objects.all()
        queryset = queryset.filter(owner=self.request.user, name=name)
        if not queryset.exists():
            response_data = {'namepitchdetectionparam': ["This parameter name does not exists"]}
            raise ValidationError(response_data)
        return(queryset.first())

    def get_stepdetectionparam_instance(self, name):
        queryset = StepDetectionParam.objects.all()
        queryset = queryset.filter(owner=self.request.user, name=name)
        if not queryset.exists():
            response_data = {'namestepdetectionparam': ["This parameter name does not exists"]}
            raise ValidationError(response_data)
        return(queryset.first())

    def get_rythmdetectionparam_instance(self, name):
        queryset = RythmDetectionParam.objects.all()
        queryset = queryset.filter(owner=self.request.user, name=name)
        if not queryset.exists():
            response_data = {'namerythmdetectionparam': ["This parameter name does not exists"]}
            raise ValidationError(response_data)
        return(queryset.first())

    def post_globalparam(self, serializer):
        name_globalparam = serializer.validated_data.get("nameglobalparam")
        instance_globalparam = self.get_globalparam_instance(name_globalparam)
        name_pitchdetectionparam = instance_globalparam.namepitchdetectionparam
        name_stepdetectionparam = instance_globalparam.namestepdetectionparam
        name_rythmdetectionparam = instance_globalparam.namerythmdetectionparam
        instance_pdp = self.get_pitchdetectionparam_instance(name_pitchdetectionparam)
        instance_sdp = self.get_stepdetectionparam_instance(name_stepdetectionparam)
        instance_rdp = self.get_rythmdetectionparam_instance(name_rythmdetectionparam)
        return(instance_pdp, instance_sdp, instance_rdp)

    def post_intermediateparams(self, serializer):
        name_pitchdetectionparam = serializer.validated_data.get('namepitchdetectionparam')
        name_stepdetectionparam = serializer.validated_data.get('namestepdetectionparam')
        name_rythmdetectionparam = serializer.validated_data.get('namerythmdetectionparam')
        instance_pdp = self.get_pitchdetectionparam_instance(name_pitchdetectionparam)
        instance_sdp = self.get_stepdetectionparam_instance(name_stepdetectionparam)
        instance_rdp = self.get_rythmdetectionparam_instance(name_rythmdetectionparam)
        return(instance_pdp, instance_sdp, instance_rdp)

    def post(self, request, pk):
        # Check if the project id exists
        project_instance = self.get_object()
        # Check if the number of process for this user is exceed
        self.check_userexceedprocessnumber(raise_exception=True)
        # Check if a process is already running for this project
        self.check_processalreadyrunning(raise_exception=True)
        # Check if the parameters are ok
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ContainsNGP = serializer.validated_data.__contains__('nameglobalparam')
        ContainsNPDP = serializer.validated_data.__contains__('namepitchdetectionparam')
        ContainsNSTP = serializer.validated_data.__contains__('namestepdetectionparam')
        ContainsNRDP = serializer.validated_data.__contains__('namerythmdetectionparam')
        ContainsALLP = ContainsNPDP and ContainsNSTP and ContainsNRDP

        if ContainsNGP:
            instance_pdp, instance_sdp, instance_rdp = self.post_globalparam(serializer)
        elif ContainsALLP:
            instance_pdp, instance_sdp, instance_rdp = self.post_intermediateparams(serializer)
        else:
            response_data = {}
            response_data['nameglobalparam'] = ["This field is required unless you provide all the other fields below"]
            response_data['namepitchdetectionparam'] = ["Required if the field 'nameglobalparam' is not provided"]
            response_data['namestepdetectionparam'] = ["Required if the field 'nameglobalparam' is not provided"]
            response_data['namerythmdetectionparam'] = ["Required if the field 'nameglobalparam' is not provided"]
            return(Response(response_data, status=status.HTTP_400_BAD_REQUEST))

        # Delete past results if exists
        if(hasattr(project_instance, "pitchdetectionresult")):
            project_instance.pitchdetectionresult.delete()

        pitchserializer = PitchDetectionSerializer(instance_pdp)
        stepserializer = StepDetectionSerializer(instance_sdp)
        rythmserializer = RythmDetectionSerializer(instance_rdp)
        # Run the conversion
        task = rundirectconversion.delay(project_instance.id, pitchserializer.data, stepserializer.data, rythmserializer.data)
        ProjectProcess.objects.create(owner=project_instance.owner,
                                      project=project_instance,
                                      task_name="direct",
                                      task_id=task.id)
        return Response({'task_id': task.id}, status=status.HTTP_201_CREATED)


class FreeConversion(generics.GenericAPIView):
    serializer_class = FreeConversionSerializer
    permission_classes = (permissions.AllowAny,)

    def save_file(self, audiofile):
        filename = str(uuid.uuid4())
        fullpathfilename = os.path.join(settings.MEDIA_ROOT, 'freeconvertertempfiles', filename + ".wav")
        while(os.path.isfile(fullpathfilename)):
            fullpathfilename = os.path.join(settings.MEDIA_ROOT, 'freeconvertertempfiles', filename + "wav")

        if not os.path.exists(os.path.dirname(fullpathfilename)):
            # Guard against race condition
            try:
                os.makedirs(os.path.dirname(fullpathfilename))
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise

        with open(fullpathfilename, 'wb+') as outfile:
            for chunk in audiofile.chunks():
                outfile.write(chunk)
        return(fullpathfilename)

    def check_file_length(self, file, raise_exception=False):
        try:
            with wave.open(file, mode='r') as wavefile:
                Fe_hz = wavefile.getframerate()
                NbSamples = wavefile.getnframes()
                Length_s = NbSamples / Fe_hz
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

    def check_file_size(self, file, raise_exception=False):
        FileSize = os.path.getsize(file)
        if(FileSize > settings.DATA_UPLOAD_MAX_MEMORY_SIZE):
            if(raise_exception):
                response_data = {'audio': ["Invalid audio format"]}
                raise ValidationError(response_data)
            return(True)
        return(False)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if(serializer.validated_data.__contains__('timestart_s')):
            timestart_s = serializer.validated_data.get('timestart_s')
        else:
            timestart_s = None
        if(serializer.validated_data.__contains__('timestop_s')):
            timestop_s = serializer.validated_data.get('timestop_s')
        else:
            timestop_s = None
        tempfile = serializer.validated_data.get('file')
        savefilepath = self.save_file(tempfile)
        self.check_file_length(savefilepath, raise_exception=True)
        self.check_file_size(savefilepath, raise_exception=True)
        email = serializer.validated_data.get('email')
        task = runfreeconversion.delay(savefilepath, email, timestart_s, timestop_s)
        return Response({'task_id': task.id}, status=status.HTTP_201_CREATED)
