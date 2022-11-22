from rest_framework import serializers
from api_manage_parameters.models import PitchDetectionParam
from api_manage_parameters.models import StepDetectionParam
from api_manage_parameters.models import RythmDetectionParam
from api_manage_parameters.models import GlobalParam
from api_manage_parameters.validators import ParameterNameValidator


class CreatePitchDetectionParamSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = PitchDetectionParam
        fields = tuple([field.name for field in PitchDetectionParam._meta.get_fields() if field.name != 'owner'])


class CreateStepDetectionParamSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = StepDetectionParam
        fields = tuple([field.name for field in StepDetectionParam._meta.get_fields() if field.name != 'owner'])


class CreateRythmDetectionParamSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = RythmDetectionParam
        fields = tuple([field.name for field in RythmDetectionParam._meta.get_fields() if field.name != 'owner'])


class CreateGlobalParamSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = GlobalParam
        fields = tuple([field.name for field in GlobalParam._meta.get_fields() if field.name != 'owner'])


class PitchDetectionParamSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    # owner = serializers.ReadOnlyField(source='owner.username')
    name = serializers.CharField(max_length=100, required=False, validators=[ParameterNameValidator])

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = PitchDetectionParam
        fields = tuple([field.name for field in PitchDetectionParam._meta.get_fields() if field.name != 'owner'])


class StepDetectionParamSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    # owner = serializers.ReadOnlyField(source='owner.username')
    name = serializers.CharField(max_length=100, required=False, validators=[ParameterNameValidator])

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = StepDetectionParam
        fields = tuple([field.name for field in StepDetectionParam._meta.get_fields() if field.name != 'owner'])


class RythmDetectionParamSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    # owner = serializers.ReadOnlyField(source='owner.username')
    name = serializers.CharField(max_length=100, required=False, validators=[ParameterNameValidator])

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = RythmDetectionParam
        fields = tuple([field.name for field in RythmDetectionParam._meta.get_fields() if field.name != 'owner'])


class GlobalParamSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    # owner = serializers.ReadOnlyField(source='owner.username')
    name = serializers.CharField(max_length=100, required=False, validators=[ParameterNameValidator])

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = GlobalParam
        fields = tuple([field.name for field in GlobalParam._meta.get_fields() if field.name != 'owner'])
