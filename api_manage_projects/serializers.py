from rest_framework import serializers

from api_manage_parameters.validators import ParameterNameValidator

from api_manage_projects.models import Project
from api_manage_projects.models import ProjectPitchDetectionParam
from api_manage_projects.models import ProjectStepDetectionParam
from api_manage_projects.models import ProjectRythmDetectionParam

from api_manage_projects.models import PitchDetectionResult
from api_manage_projects.models import StepDetectionResult
from api_manage_projects.models import RythmDetectionResult

from api_manage_projects.validators import ProjectNameValidator

from api_manage_parameters.validators import validators_timestart_s
from api_manage_parameters.validators import validators_timestop_s


class CreateProjectSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    # owner = serializers.ReadOnlyField(source='owner.username')
    date_created = serializers.ReadOnlyField()
    state = serializers.ReadOnlyField()

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = Project
        # fields = '__all__'
        # fields = ('id','owner','name','date_created','state','audiofile',)
        fields = ('id', 'name', 'date_created', 'audiofile', 'instrument', 'state', )
        extra_kwargs = {'audiofile': {'write_only': True}}


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    name = serializers.CharField(max_length=100, required=False, validators=[ProjectNameValidator, ])
    instrument = serializers.CharField(max_length=100, required=False)
    date_created = serializers.ReadOnlyField()

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = Project
        fields = ('id', 'name', 'date_created', 'instrument', )


# FileTypeRegexValidator = RegexValidator(regex='^pitch$|^musicxml$|^midi$|^midinorythm$|^audio$',flags=2, message='Accepted strings: pitch, musicxml, midi, midinorythm, audio', code='nomatch')
# class DownloadSerializer(serializers.Serializer):
#     """Serializer to map the Model instance into JSON format."""
#     filetype = serializers.CharField(max_length=20, required=True,validators=[FileTypeRegexValidator])


class PitchDetectionSerializer(serializers.ModelSerializer):
    timestart_s = serializers.FloatField(validators=validators_timestart_s, required=False)
    timestop_s = serializers.FloatField(validators=validators_timestop_s, required=False)

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = ProjectPitchDetectionParam
        exclude = ('pitchdetectionresult', )
        extra_kwargs = {'windowtimesize_s': {'required': True},
                        'sonogramperiod_s': {'required': True},
                        'f0_hz': {'required': True},
                        'freqmin_hz': {'required': True},
                        'freqmax_hz': {'required': True},
                        'cutoff': {'required': True},
                        'smallcutoff': {'required': True}, }


class StepDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = ProjectStepDetectionParam
        exclude = ('stepdetectionresult', )
        extra_kwargs = {'medianfiltersize_s': {'required': True},
                        'thresholdenergyon_db': {'required': True},
                        'thresholdenergyoff_db': {'required': True},
                        'maxpitchvariation_st': {'required': True},
                        'minimumtimesize_s': {'required': True},
                        'minnotesize_s': {'required': True},
                        'minnotediff_st': {'required': True},
                        'lmhgaussian_st': {'required': True}, }


class RythmDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = ProjectRythmDetectionParam
        exclude = ('rythmdetectionresult', )
        extra_kwargs = {'delaymin_s': {'required': True},
                        'delaymax_s': {'required': True},
                        'maxdelayvar': {'required': True},
                        'errormax': {'required': True},
                        'onenoteonebeat': {'required': True},
                        'onenotetwobeat': {'required': True},
                        'onenotethreebeat': {'required': True},
                        'onenotefourbeat': {'required': True},
                        'onenotefivebeat': {'required': True},
                        'onenotesixbeat': {'required': True},
                        'onenotesevenbeat': {'required': True},
                        'onenoteeightbeat': {'required': True},
                        'onerestonebeat': {'required': True},
                        'oneresttwobeat': {'required': True},
                        'onerestthreebeat': {'required': True},
                        'onerestfourbeat': {'required': True},
                        'onerestfivebeat': {'required': True},
                        'onerestsixbeat': {'required': True},
                        'onerestsevenbeat': {'required': True},
                        'oneresteightbeat': {'required': True},
                        'en_en': {'required': True},
                        'er_en': {'required': True},
                        'en_er': {'required': True},
                        'den_sn': {'required': True},
                        'sn_den': {'required': True},
                        'dqn_en': {'required': True},
                        'qr_er_en': {'required': True},
                        'dqn_er': {'required': True},
                        'en_en_qn': {'required': True},
                        'qn_dqn_en': {'required': True},
                        'qr_qr_er_en': {'required': True},
                        'qn_dqn_er': {'required': True},
                        'en_en_hn': {'required': True},
                        'hn_dqn_en': {'required': True},
                        'qr_qr_qr_er_en': {'required': True},
                        'hn_dqn_er': {'required': True},
                        'en_en_dhn': {'required': True},
                        'en_sn_sn': {'required': True},
                        'er_sn_sn': {'required': True},
                        'sn_sn_en': {'required': True},
                        'sn_sn_er': {'required': True},
                        'sn_en_sn': {'required': True},
                        't_en_en_en': {'required': True},
                        't_en_den_sn': {'required': True},
                        't_en_sn_den': {'required': True},
                        't_sn_en_den': {'required': True},
                        't_sn_den_en': {'required': True},
                        't_den_en_sn': {'required': True},
                        't_den_sn_en': {'required': True},
                        'en_qn_en': {'required': True},
                        'dqn_sn_sn': {'required': True},
                        'qn_dqn_sn_sn': {'required': True},
                        'hn_dqn_sn_sn': {'required': True},
                        'sn_sn_sn_sn': {'required': True}, }


class DirectConversionSerializer(serializers.Serializer):
    nameglobalparam = serializers.CharField(max_length=100, validators=[ParameterNameValidator, ], required=False)
    namepitchdetectionparam = serializers.CharField(max_length=100, validators=[ParameterNameValidator, ], required=False)
    namestepdetectionparam = serializers.CharField(max_length=100, validators=[ParameterNameValidator, ], required=False)
    namerythmdetectionparam = serializers.CharField(max_length=100, validators=[ParameterNameValidator, ], required=False)


class CheckListTaskStateSerializer(serializers.Serializer):
    task_ids = serializers.ListField(child=serializers.UUIDField(), required=True)


class PitchResultSerializer(serializers.ModelSerializer):
    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = PitchDetectionResult
        exclude = ('id', 'project', )


class StepResultSerializer(serializers.ModelSerializer):
    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = StepDetectionResult
        exclude = ('id', 'pitchdetectionresult', )


class RythmResultSerializer(serializers.ModelSerializer):
    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = RythmDetectionResult
        exclude = ('id', 'stepdetectionresult', )


class FreeConversionSerializer(serializers.Serializer):
    file = serializers.FileField(allow_empty_file=False, required=True)
    email = serializers.EmailField(required=True)
    timestart_s = serializers.FloatField(validators=validators_timestart_s, required=False)
    timestop_s = serializers.FloatField(validators=validators_timestop_s, required=False)
