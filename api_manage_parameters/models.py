from django.db import models
from django.dispatch import receiver
from django.contrib.auth.models import User

from api_manage_parameters.validators import ParameterNameValidator

# PITCH
from api_manage_parameters.validators import validators_windowtimesize_s
from api_manage_parameters.validators import validators_sonogramperiod_s
from api_manage_parameters.validators import validators_f0_hz
from api_manage_parameters.validators import validators_freqmin_hz
from api_manage_parameters.validators import validators_freqmax_hz
from api_manage_parameters.validators import validators_cutoff
from api_manage_parameters.validators import validators_smallcutoff

# STEP
from api_manage_parameters.validators import validators_medianfiltersize_s
from api_manage_parameters.validators import validators_thresholdenergyon_db
from api_manage_parameters.validators import validators_thresholdenergyoff_db
from api_manage_parameters.validators import validators_maxpitchvariation_st
from api_manage_parameters.validators import validators_minimumtimesize_s
from api_manage_parameters.validators import validators_minnotesize_s
from api_manage_parameters.validators import validators_minnotediff_st
from api_manage_parameters.validators import validators_lmhgaussian_st

# RYTHM
from api_manage_parameters.validators import validators_delaymin_s
from api_manage_parameters.validators import validators_delaymax_s
from api_manage_parameters.validators import validators_maxdelayvar
from api_manage_parameters.validators import validators_errormax

# Abstract base classes
# Warning : DO NOT SET SAME FIELD NAME FOR THE ABSTRACT BASE CLASSES BELOW !

DEFAULT_PARAMETER_NAME = "default"


class AbstractPitchDetectionParam(models.Model):
    windowtimesize_s = models.FloatField(default=20e-3, validators=validators_windowtimesize_s)
    sonogramperiod_s = models.FloatField(default=1e-3, validators=validators_sonogramperiod_s)
    f0_hz = models.FloatField(default=32.7032, validators=validators_f0_hz)
    freqmin_hz = models.FloatField(default=80, validators=validators_freqmin_hz)
    freqmax_hz = models.FloatField(default=5000, validators=validators_freqmax_hz)
    cutoff = models.FloatField(default=0.97, validators=validators_cutoff)
    smallcutoff = models.FloatField(default=0.5, validators=validators_smallcutoff)

    class Meta:
        abstract = True


class AbstractStepDetectionParam(models.Model):
    medianfiltersize_s = models.FloatField(default=51e-3, validators=validators_medianfiltersize_s)
    thresholdenergyon_db = models.FloatField(default=25.0, validators=validators_thresholdenergyon_db)
    thresholdenergyoff_db = models.FloatField(default=30.0, validators=validators_thresholdenergyoff_db)
    maxpitchvariation_st = models.FloatField(default=1, validators=validators_maxpitchvariation_st)
    minimumtimesize_s = models.FloatField(default=50e-3, validators=validators_minimumtimesize_s)
    minnotesize_s = models.FloatField(default=100e-3, validators=validators_minnotesize_s)
    minnotediff_st = models.FloatField(default=0.5, validators=validators_minnotediff_st)
    lmhgaussian_st = models.FloatField(default=0.5, validators=validators_lmhgaussian_st)

    class Meta:
        abstract = True


class AbstractRythmDetectionParam(models.Model):
    delaymin_s = models.FloatField(default=0.3, validators=validators_delaymin_s)
    delaymax_s = models.FloatField(default=1.5, validators=validators_delaymax_s)
    maxdelayvar = models.FloatField(default=0.5, validators=validators_maxdelayvar)
    errormax = models.FloatField(default=10, validators=validators_errormax)
    # COMBINATIONS
    # 1 NOTES
    onenoteonebeat = models.BooleanField(default=True)
    onenotetwobeat = models.BooleanField(default=True)
    onenotethreebeat = models.BooleanField(default=True)
    onenotefourbeat = models.BooleanField(default=True)
    onenotefivebeat = models.BooleanField(default=True)
    onenotesixbeat = models.BooleanField(default=True)
    onenotesevenbeat = models.BooleanField(default=True)
    onenoteeightbeat = models.BooleanField(default=True)
    onerestonebeat = models.BooleanField(default=True)
    oneresttwobeat = models.BooleanField(default=True)
    onerestthreebeat = models.BooleanField(default=True)
    onerestfourbeat = models.BooleanField(default=True)
    onerestfivebeat = models.BooleanField(default=True)
    onerestsixbeat = models.BooleanField(default=True)
    onerestsevenbeat = models.BooleanField(default=True)
    oneresteightbeat = models.BooleanField(default=True)
    # 2 NOTES
    # 1 BEAT
    en_en = models.BooleanField(default=True)
    er_en = models.BooleanField(default=True)
    en_er = models.BooleanField(default=True)
    den_sn = models.BooleanField(default=True)
    sn_den = models.BooleanField(default=True)
    # 2 BEATS
    dqn_en = models.BooleanField(default=True)
    qr_er_en = models.BooleanField(default=True)
    dqn_er = models.BooleanField(default=True)
    en_en_qn = models.BooleanField(default=True)
    # 3 BEATS
    qn_dqn_en = models.BooleanField(default=True)
    qr_qr_er_en = models.BooleanField(default=True)
    qn_dqn_er = models.BooleanField(default=True)
    en_en_hn = models.BooleanField(default=True)
    # 4 BEATS
    hn_dqn_en = models.BooleanField(default=True)
    qr_qr_qr_er_en = models.BooleanField(default=True)
    hn_dqn_er = models.BooleanField(default=True)
    en_en_dhn = models.BooleanField(default=True)

    # 3 NOTES
    # 1 BEAT
    en_sn_sn = models.BooleanField(default=True)
    er_sn_sn = models.BooleanField(default=True)
    sn_sn_en = models.BooleanField(default=True)
    sn_sn_er = models.BooleanField(default=True)
    sn_en_sn = models.BooleanField(default=True)
    t_en_en_en = models.BooleanField(default=True)
    t_en_den_sn = models.BooleanField(default=True)
    t_en_sn_den = models.BooleanField(default=True)
    t_sn_en_den = models.BooleanField(default=True)
    t_sn_den_en = models.BooleanField(default=True)
    t_den_en_sn = models.BooleanField(default=True)
    t_den_sn_en = models.BooleanField(default=True)
    # 2 BEATS
    en_qn_en = models.BooleanField(default=True)
    dqn_sn_sn = models.BooleanField(default=True)
    # 3 BEATS
    qn_dqn_sn_sn = models.BooleanField(default=True)
    # 4 BEATS
    hn_dqn_sn_sn = models.BooleanField(default=True)
    # 4 NOTES
    sn_sn_sn_sn = models.BooleanField(default=True)

    class Meta:
        abstract = True
#################################


class PitchDetectionParam(AbstractPitchDetectionParam):
    name = models.CharField(max_length=100, validators=[ParameterNameValidator])
    owner = models.ForeignKey('auth.User', related_name='pitchdetectionparams', on_delete=models.CASCADE)

    class Meta(object):
        unique_together = ('name', 'owner', )

    def __str__(self):
        """Return the name of the parameter"""
        return "{}".format(self.name)


class StepDetectionParam(AbstractStepDetectionParam):
    name = models.CharField(max_length=100, validators=[ParameterNameValidator])
    owner = models.ForeignKey('auth.User', related_name='stepdetectionparams', on_delete=models.CASCADE)

    class Meta(object):
        unique_together = ('name', 'owner', )

    def __str__(self):
        """Return the name of the parameter"""
        return "{}".format(self.name)


class RythmDetectionParam(AbstractRythmDetectionParam):
    name = models.CharField(max_length=100, validators=[ParameterNameValidator])
    owner = models.ForeignKey('auth.User', related_name='rythmdetectionparams', on_delete=models.CASCADE)

    class Meta(object):
        unique_together = ('name', 'owner', )

    def __str__(self):
        """Return the name of the parameter"""
        return "{}".format(self.name)


class GlobalParam(models.Model):
    name = models.CharField(max_length=100, validators=[ParameterNameValidator])
    owner = models.ForeignKey('auth.User', related_name='globalparams', on_delete=models.CASCADE)
    namepitchdetectionparam = models.CharField(max_length=100, default=DEFAULT_PARAMETER_NAME, validators=[ParameterNameValidator])
    namestepdetectionparam = models.CharField(max_length=100, default=DEFAULT_PARAMETER_NAME, validators=[ParameterNameValidator])
    namerythmdetectionparam = models.CharField(max_length=100, default=DEFAULT_PARAMETER_NAME, validators=[ParameterNameValidator])

    class Meta(object):
        unique_together = ('name', 'owner', )

    def __str__(self):
        """Return the name of the parameter"""
        return "{}".format(self.name)


# Automatically create default parameter when a new user is created

@receiver(models.signals.post_save, sender=User)
def auto_create_default_param_on_save_user(sender, instance, created, **kwargs):
    """
    Create default parameters
    when a user is created
    """
    if created:
        PitchDetectionParam.objects.create(owner=instance, name=DEFAULT_PARAMETER_NAME)
        StepDetectionParam.objects.create(owner=instance, name=DEFAULT_PARAMETER_NAME)
        RythmDetectionParam.objects.create(owner=instance, name=DEFAULT_PARAMETER_NAME)
        GlobalParam.objects.create(owner=instance, name=DEFAULT_PARAMETER_NAME)


# Automatically change the name of the parameter to 'default' in the global parameter
# if a sub parameter is deleted
########################################################################
@receiver(models.signals.post_delete, sender=PitchDetectionParam)
def auto_update_global_param_on_delete_pitchdetectionparam(sender, instance, **kwargs):
    """
    Update global parameter
    when a sub parameter is deleted
    """
    queryset = GlobalParam.objects.all()
    queryset = queryset.filter(owner=instance.owner)
    queryset = queryset.filter(namepitchdetectionparam=instance.name)
    for data in queryset:
        data.namepitchdetectionparam = DEFAULT_PARAMETER_NAME
        data.save()


@receiver(models.signals.post_delete, sender=StepDetectionParam)
def auto_update_global_param_on_delete_stepdetectionparam(sender, instance, **kwargs):
    """
    Update global parameter
    when a sub parameter is deleted
    """
    queryset = GlobalParam.objects.all()
    queryset = queryset.filter(owner=instance.owner)
    queryset = queryset.filter(namestepdetectionparam=instance.name)
    for data in queryset:
        data.namestepdetectionparam = DEFAULT_PARAMETER_NAME
        data.save()


@receiver(models.signals.post_delete, sender=RythmDetectionParam)
def auto_update_global_param_on_delete_rythmdetectionparam(sender, instance, **kwargs):
    """
    Update global parameter
    when a sub parameter is deleted
    """
    queryset = GlobalParam.objects.all()
    queryset = queryset.filter(owner=instance.owner)
    queryset = queryset.filter(namerythmdetectionparam=instance.name)
    for data in queryset:
        data.namerythmdetectionparam = DEFAULT_PARAMETER_NAME
        data.save()
