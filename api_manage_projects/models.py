from django.db import models
from django.contrib.postgres.fields import ArrayField
import datetime
from django.dispatch import receiver
import os
import shutil
from celery.task.control import revoke

from api_manage_parameters.models import AbstractPitchDetectionParam
from api_manage_parameters.models import AbstractStepDetectionParam
from api_manage_parameters.models import AbstractRythmDetectionParam

from api_manage_projects.validators import ProjectNameValidator
from api_manage_projects.validators import ProjectInstrumentValidator

from api_manage_parameters.validators import validators_timestart_s
from api_manage_parameters.validators import validators_timestop_s


def user_project_folder_path(project_instance):
    owner = project_instance.owner
    UserFolder = owner.profile.user_folder_path()
    ProjectFolderName = '{0}'.format(project_instance.name)
    ProjectFullPath = os.path.join(UserFolder, ProjectFolderName)
    return(ProjectFullPath)


def user_project_audio_path(instance, filename):
    projectfullpath = user_project_folder_path(instance)
    Filename = "audio.wav"
    FileFullPath = os.path.join(projectfullpath, Filename)
    return FileFullPath


def user_project_midifile_path(rythmdetectionresult_instance, filename):
    projectinstance = rythmdetectionresult_instance.stepdetectionresult.pitchdetectionresult.project
    projectfullpath = user_project_folder_path(projectinstance)
    Filename = "score.mid"
    FileFullPath = os.path.join(projectfullpath, Filename)
    return FileFullPath


def user_project_midifile_norythm_path(rythmdetectionresult_instance, filename):
    projectinstance = rythmdetectionresult_instance.stepdetectionresult.pitchdetectionresult.project
    projectfullpath = user_project_folder_path(projectinstance)
    Filename = "score_norythm.mid"
    FileFullPath = os.path.join(projectfullpath, Filename)
    return FileFullPath


def user_project_musicxmlfile_path(rythmdetectionresult_instance, filename):
    projectinstance = rythmdetectionresult_instance.stepdetectionresult.pitchdetectionresult.project
    projectfullpath = user_project_folder_path(projectinstance)
    Filename = "score.xml"
    FileFullPath = os.path.join(projectfullpath, Filename)
    return FileFullPath


class Project(models.Model):
    name = models.CharField(max_length=100, blank=False, validators=[ProjectNameValidator, ])
    owner = models.ForeignKey('auth.User', related_name='projects', on_delete=models.CASCADE)
    audiofile = models.FileField(upload_to=user_project_audio_path)
    date_created = models.DateField(default=datetime.date.today)
    instrument = models.CharField(max_length=100, blank=False, validators=[ProjectInstrumentValidator, ])

    def get_projectstate(self):
        if not (hasattr(self, 'pitchdetectionresult')):
            return(0)
        pitchdetectionresultinstance = self.pitchdetectionresult
        if not (hasattr(pitchdetectionresultinstance, 'stepdetectionresult')):
            return(1)
        stepdetectionresultinstance = pitchdetectionresultinstance.stepdetectionresult
        if not (hasattr(stepdetectionresultinstance, 'rythmdetectionresult')):
            return(2)
        return(3)

    def is_processrunning(self):
        if(hasattr(self, 'projectprocess')):
            return(True)
        return(False)

    class Meta(object):
        unique_together = ('name', 'owner',)

    def __str__(self):
        """Return the name of the parameter"""
        return "{}".format(self.name)


class ProjectProcess(models.Model):
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    project = models.OneToOneField(Project, on_delete=models.CASCADE)
    task_name = models.CharField(max_length=100, blank=False)
    task_id = models.CharField(max_length=100)


# Results of a project ###
##########################################################################
class PitchDetectionResult(models.Model):
    # corresponding project
    project = models.OneToOneField(Project, on_delete=models.CASCADE)
    # Result of this step
    pitch_st = ArrayField(models.FloatField(), null=True, blank=True)
    energy_db = ArrayField(models.FloatField(), null=True, blank=True)
    te_s = models.FloatField(default=1)
    f0_hz = models.FloatField(default=1)
    timestart_s = models.FloatField(null=True, blank=True, validators=validators_timestart_s)
    timestop_s = models.FloatField(null=True, blank=True, validators=validators_timestop_s)


class ProjectPitchDetectionParam(AbstractPitchDetectionParam):
    pitchdetectionresult = models.OneToOneField(PitchDetectionResult, on_delete=models.CASCADE)
    timestart_s = models.FloatField(null=True, blank=True, validators=validators_timestart_s)
    timestop_s = models.FloatField(null=True, blank=True, validators=validators_timestop_s)

    @classmethod
    def create_from_param(cls, param, pdr_instance, timestart_s=None, timestop_s=None):
        ppdp = cls(
            windowtimesize_s=param.windowtimesize_s,
            sonogramperiod_s=param.sonogramperiod_s,
            f0_hz=param.f0_hz,
            freqmin_hz=param.freqmin_hz,
            freqmax_hz=param.freqmax_hz,
            cutoff=param.cutoff,
            smallcutoff=param.smallcutoff,
            timestart_s=timestart_s,
            timestop_s=timestop_s,
            pitchdetectionresult=pdr_instance)
        ppdp.save()
        return ppdp


class StepDetectionResult(models.Model):
    # corresponding pitch result
    pitchdetectionresult = models.OneToOneField(PitchDetectionResult, on_delete=models.CASCADE)
    # Result of this step
    type_b = ArrayField(models.BooleanField(), null=True, blank=True)
    length_s = ArrayField(models.FloatField(), null=True, blank=True)
    f0_hz = ArrayField(models.FloatField(), null=True, blank=True)
    pitch_st = ArrayField(models.FloatField(), null=True, blank=True)
    energy_db = ArrayField(models.FloatField(), null=True, blank=True)
    linked_b = ArrayField(models.BooleanField(), null=True, blank=True)
    offset_s = models.FloatField(null=True, blank=True)


class ProjectStepDetectionParam(AbstractStepDetectionParam):
    stepdetectionresult = models.OneToOneField(StepDetectionResult, on_delete=models.CASCADE)

    @classmethod
    def create_from_param(cls, param, sdr_instance):
        psdp = cls(
            medianfiltersize_s=param.medianfiltersize_s,
            thresholdenergyon_db=param.thresholdenergyon_db,
            thresholdenergyoff_db=param.thresholdenergyoff_db,
            maxpitchvariation_st=param.maxpitchvariation_st,
            minimumtimesize_s=param.minimumtimesize_s,
            minnotesize_s=param.minnotesize_s,
            minnotediff_st=param.minnotediff_st,
            lmhgaussian_st=param.lmhgaussian_st,
            stepdetectionresult=sdr_instance)
        psdp.save()
        return psdp


class RythmDetectionResult(models.Model):
    # corresponding step result
    stepdetectionresult = models.OneToOneField(StepDetectionResult, on_delete=models.CASCADE)
    # Result of this step
    midifile = models.FileField(upload_to=user_project_midifile_path, null=True, blank=True)
    midifile_norythm = models.FileField(upload_to=user_project_midifile_norythm_path, null=True, blank=True)
    musicxmlfile = models.FileField(upload_to=user_project_musicxmlfile_path, null=True, blank=True)


class ProjectRythmDetectionParam(AbstractRythmDetectionParam):
    rythmdetectionresult = models.OneToOneField(RythmDetectionResult, on_delete=models.CASCADE)

    @classmethod
    def create_from_param(cls, param, rdr_instance):
        prdp = cls(
            delaymin_s=param.delaymin_s,
            delaymax_s=param.delaymax_s,
            maxdelayvar=param.maxdelayvar,
            errormax=param.errormax,
            onenoteonebeat=param.onenoteonebeat,
            onenotetwobeat=param.onenotetwobeat,
            onenotethreebeat=param.onenotethreebeat,
            onenotefourbeat=param.onenotefourbeat,
            onenotefivebeat=param.onenotefivebeat,
            onenotesixbeat=param.onenotesixbeat,
            onenotesevenbeat=param.onenotesevenbeat,
            onenoteeightbeat=param.onenoteeightbeat,
            onerestonebeat=param.onerestonebeat,
            oneresttwobeat=param.oneresttwobeat,
            onerestthreebeat=param.onerestthreebeat,
            onerestfourbeat=param.onerestfourbeat,
            onerestfivebeat=param.onerestfivebeat,
            onerestsixbeat=param.onerestsixbeat,
            onerestsevenbeat=param.onerestsevenbeat,
            oneresteightbeat=param.oneresteightbeat,
            en_en=param.en_en,
            er_en=param.er_en,
            en_er=param.en_er,
            den_sn=param.den_sn,
            sn_den=param.sn_den,
            dqn_en=param.dqn_en,
            qr_er_en=param.qr_er_en,
            dqn_er=param.dqn_er,
            en_en_qn=param.en_en_qn,
            qn_dqn_en=param.qn_dqn_en,
            qr_qr_er_en=param.qr_qr_er_en,
            qn_dqn_er=param.qn_dqn_er,
            en_en_hn=param.en_en_hn,
            hn_dqn_en=param.hn_dqn_en,
            qr_qr_qr_er_en=param.qr_qr_qr_er_en,
            hn_dqn_er=param.hn_dqn_er,
            en_en_dhn=param.en_en_dhn,
            en_sn_sn=param.en_sn_sn,
            er_sn_sn=param.er_sn_sn,
            sn_sn_en=param.sn_sn_en,
            sn_sn_er=param.sn_sn_er,
            sn_en_sn=param.sn_en_sn,
            t_en_en_en=param.t_en_en_en,
            t_en_den_sn=param.t_en_den_sn,
            t_en_sn_den=param.t_en_sn_den,
            t_sn_en_den=param.t_sn_en_den,
            t_sn_den_en=param.t_sn_den_en,
            t_den_en_sn=param.t_den_en_sn,
            t_den_sn_en=param.t_den_sn_en,
            en_qn_en=param.en_qn_en,
            dqn_sn_sn=param.dqn_sn_sn,
            qn_dqn_sn_sn=param.qn_dqn_sn_sn,
            hn_dqn_sn_sn=param.hn_dqn_sn_sn,
            sn_sn_sn_sn=param.sn_sn_sn_sn,
            rythmdetectionresult=rdr_instance)
        prdp.save()
        return prdp
##########################################################################

# Automatically create corresponding parameters models when creating results
###############################################################################
# @receiver(models.signals.post_save, sender=PitchDetectionResult)
# def create_or_update_pitchdetectionresult_param(sender, instance, created, **kwargs):
#     if created:
#         ProjectPitchDetectionParam.objects.create(pitchdetectionresult=instance)
#     instance.projectpitchdetectionparam.save()
#
# @receiver(models.signals.post_save, sender=StepDetectionResult)
# def create_or_update_stepdetectionresult_param(sender, instance, created, **kwargs):
#     if created:
#         ProjectStepDetectionParam.objects.create(stepdetectionresult=instance)
#     instance.projectstepdetectionparam.save()
#
# @receiver(models.signals.post_save, sender=FinalResult)
# def create_or_update_finalresult_param(sender, instance, created, **kwargs):
#     if created:
#         ProjectRythmDetectionParam.objects.create(finalresult=instance)
#     instance.projectrythmdetectionparam.save()
###############################################################################


# When a new project is created
#   - Automatically decrement the number of project per day created
###############################################################################
@receiver(models.signals.post_save, sender=Project)
def auto_decrement_nbproject_on_create_project(sender, instance, **kwargs):
    instance_user = instance.owner
    instance_user.profile.projects_remaining = instance_user.profile.projects_remaining - 1
    instance_user.profile.save()


# When deleting a project:
#    - Automatically delete project folder
#    - Automatically delete project task if exists
###############################################################################

@receiver(models.signals.post_delete, sender=Project)
def auto_delete_file_on_delete_project(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `Project` object is deleted.
    """
    fullfolderpath = user_project_folder_path(instance)
    if os.path.exists(fullfolderpath):
        shutil.rmtree(fullfolderpath)


@receiver(models.signals.pre_delete, sender=Project)
def auto_revoke_task_on_delete_project(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `Project` object is deleted.
    """
    if(hasattr(instance, 'projectprocess')):
        task_id = instance.projectprocess.task_id
        revoke(task_id, terminate=True)
###############################################################################


# Automatically delete audio file when deleting the corresponding results
###############################################################################
@receiver(models.signals.post_delete, sender=RythmDetectionResult)
def auto_delete_file_on_delete_result(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `FinalResult` object is deleted.
    """
    if instance.midifile:
        if os.path.isfile(instance.midifile.path):
            instance.midifile.delete(save=False)
    if instance.midifile_norythm:
        if os.path.isfile(instance.midifile_norythm.path):
            instance.midifile_norythm.delete(save=False)
    if instance.musicxmlfile:
        if os.path.isfile(instance.musicxmlfile.path):
            instance.musicxmlfile.delete(save=False)


@receiver(models.signals.pre_save, sender=RythmDetectionResult)
def auto_delete_file_on_change_resultmidi1(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `FinalResult` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = RythmDetectionResult.objects.get(pk=instance.pk).midifile
    except RythmDetectionResult.DoesNotExist:
        return False

    try:
        old_file_path = old_file.path
    except ValueError:
        return False

    new_file = instance.midifile
    if not old_file == new_file:
        if os.path.isfile(old_file_path):
            old_file.delete(save=False)


@receiver(models.signals.pre_save, sender=RythmDetectionResult)
def auto_delete_file_on_change_resultmidi2(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `FinalResult` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = RythmDetectionResult.objects.get(pk=instance.pk).midifile_norythm
    except RythmDetectionResult.DoesNotExist:
        return False

    try:
        old_file_path = old_file.path
    except ValueError:
        return False

    new_file = instance.midifile_norythm
    if not old_file == new_file:
        if os.path.isfile(old_file_path):
            old_file.delete(save=False)


@receiver(models.signals.pre_save, sender=RythmDetectionResult)
def auto_delete_file_on_change_resultxml(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `FinalResult` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = RythmDetectionResult.objects.get(pk=instance.pk).musicxmlfile
    except RythmDetectionResult.DoesNotExist:
        return False

    try:
        old_file_path = old_file.path
    except ValueError:
        return False

    new_file = instance.musicxmlfile
    if not old_file == new_file:
        if os.path.isfile(old_file_path):
            old_file.delete(save=False)
########################################################################
