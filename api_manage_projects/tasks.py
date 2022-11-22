from __future__ import absolute_import, unicode_literals
from celery import shared_task, current_task

from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from api_manage_projects.models import user_project_audio_path
from api_manage_projects.models import ProjectProcess

from scorelisto._1_wavfilereader import AudioWav
from scorelisto._2_sonogram import Sonogram
from scorelisto._3_digitalpartition import DigitalPartition

from api_manage_projects.models import Project

from celery.signals import task_success
from celery.signals import task_failure
from celery.signals import task_revoked

from api_manage_projects.serializers import PitchDetectionSerializer
from api_manage_projects.serializers import StepDetectionSerializer
from api_manage_projects.serializers import RythmDetectionSerializer

from api_manage_projects.models import PitchDetectionResult
from api_manage_projects.models import StepDetectionResult
from api_manage_projects.models import RythmDetectionResult

from api_manage_parameters.models import AbstractPitchDetectionParam
from api_manage_parameters.models import AbstractStepDetectionParam
from api_manage_parameters.models import AbstractRythmDetectionParam


def check_pitchresults(results, raise_exception=True):
    if(len(results['pitch_st']) == 0):
        if(raise_exception):
            raise ValueError("Invalid output")
        else:
            return False
    return True


def check_stepresults(results, raise_exception=True):
    if(len(results) == 0):
        if(raise_exception):
            raise ValueError("Invalid output")
        else:
            return False
    return True


def check_rythmresults(results, raise_exception=True):
    if(results['XMLString'] == ''):
        if(raise_exception):
            raise ValueError("Invalid output")
        else:
            return False
    return True


@shared_task()
def runpitchdetection(project_id, parameters, timestart_s=None, timestop_s=None, update_method=None):
    if(update_method is None):
        update_method = current_task.update_state
    instance_project = Project.objects.get(id=project_id)
    # Parameters
    filepath = user_project_audio_path(instance_project, None)
    windowtimesize_s = parameters['windowtimesize_s']
    sonogramperiod_s = parameters['sonogramperiod_s']
    f0_hz = parameters['f0_hz']
    freqmin_hz = parameters['freqmin_hz']
    freqmax_hz = parameters['freqmax_hz']
    cutoff = parameters['cutoff']
    smallcutoff = parameters['smallcutoff']
    # Processing
    AUDIO = AudioWav(filepath)
    AUDIO.A_DefineMcLeodParameters(freqmin_hz, freqmax_hz, cutoff, smallcutoff)
    OUTPUT = AUDIO.B_ExtractSemitonegram(windowtimesize_s, sonogramperiod_s, f0_hz, timestart_s, timestop_s, update_method)
    # Checking if the ouput is correct
    check_pitchresults(OUTPUT)
    return(OUTPUT, timestart_s, timestop_s)


@shared_task()
def runstepdetection(project_id, parameters, update_method=None):
    if(update_method is None):
        update_method = current_task.update_state
    instance_project = Project.objects.get(id=project_id)
    instance_pitchresult = instance_project.pitchdetectionresult
    # Inputs
    pitch_st = instance_pitchresult.pitch_st
    energy_db = instance_pitchresult.energy_db
    te_s = instance_pitchresult.te_s
    f0_hz = instance_pitchresult.f0_hz
    # Parameters
    medianfiltersize_s = parameters['medianfiltersize_s']
    thresholdenergyon_db = parameters['thresholdenergyon_db']
    thresholdenergyoff_db = parameters['thresholdenergyoff_db']
    maxpitchvariation_st = parameters['maxpitchvariation_st']
    minimumtimesize_s = parameters['minimumtimesize_s']
    minnotesize_s = parameters['minnotesize_s']
    minnotediff_st = parameters['minnotediff_st']
    lmhgaussian_st = parameters['lmhgaussian_st']
    # Processing
    update_method(state='STARTED', meta={'progression': 0, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Loading pitch array", })
    SONO = Sonogram(pitch_st, energy_db, te_s, f0_hz)
    update_method(state='STARTED', meta={'progression': 1, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Applying median filter", })
    SONO.A_ApplyMedianFilter(medianfiltersize_s)
    update_method(state='STARTED', meta={'progression': 2, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Threshold on the energy", })
    SONO.B_Masked_AutoEnergy(thresholdenergyon_db, thresholdenergyoff_db)
    update_method(state='STARTED', meta={'progression': 3, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Maximum pitch variation", })
    SONO.C_Masked_MaximumVariation(maxpitchvariation_st)
    update_method(state='STARTED', meta={'progression': 4, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Filtering too short detections", })
    SONO.D_Masked_MinimumTimeSize(minimumtimesize_s)
    update_method(state='STARTED', meta={'progression': 5, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Detecting linked notes", })
    SONO.E_DetectGroupsOfNotes()
    update_method(state='STARTED', meta={'progression': 6, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Extracting notes", })
    SONO.F_Detectnotes(minnotesize_s, minnotediff_st, lmhgaussian_st)
    update_method(state='STARTED', meta={'progression': 7, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Generating output", })
    OUTPUT = SONO.G_GenerateAnalogPartition()
    update_method(state='STARTED', meta={'progression': 8, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Saving output", })
    # Offset of the first group of note
    offset_s = SONO.TimeOffsetFirstGroup()
    # Checking if the ouput is correct
    check_stepresults(OUTPUT)
    return(OUTPUT, offset_s)


@shared_task()
def runrythmdetection(project_id, parameters, update_method=None):
    if(update_method is None):
        update_method = current_task.update_state
    instance_project = Project.objects.get(id=project_id)
    ProjectOwner = instance_project.owner.username
    ProjectName = instance_project.name
    instance_pitchresult = instance_project.pitchdetectionresult
    instance_stepresult = instance_pitchresult.stepdetectionresult
    # Inputs
    type_b = instance_stepresult.type_b
    length_s = instance_stepresult.length_s
    pitch_st = instance_stepresult.pitch_st
    # Parameters
    delaymin_s = parameters['delaymin_s']
    delaymax_s = parameters['delaymax_s']
    maxdelayvar = parameters['maxdelayvar']
    errormax = parameters['errormax']
    combstomask = {}
    combstomask['1NOTE_1BEAT'] = not parameters['onenoteonebeat']
    combstomask['1NOTE_2BEATS'] = not parameters['onenotetwobeat']
    combstomask['1NOTE_3BEATS'] = not parameters['onenotethreebeat']
    combstomask['1NOTE_4BEATS'] = not parameters['onenotefourbeat']
    combstomask['1NOTE_5BEATS'] = not parameters['onenotefivebeat']
    combstomask['1NOTE_6BEATS'] = not parameters['onenotesixbeat']
    combstomask['1NOTE_7BEATS'] = not parameters['onenotesevenbeat']
    combstomask['1NOTE_8BEATS'] = not parameters['onenoteeightbeat']
    combstomask['1REST_1BEAT'] = not parameters['onerestonebeat']
    combstomask['1REST_2BEATS'] = not parameters['oneresttwobeat']
    combstomask['1REST_3BEATS'] = not parameters['onerestthreebeat']
    combstomask['1REST_4BEATS'] = not parameters['onerestfourbeat']
    combstomask['1REST_5BEATS'] = not parameters['onerestfivebeat']
    combstomask['1REST_6BEATS'] = not parameters['onerestsixbeat']
    combstomask['1REST_7BEATS'] = not parameters['onerestsevenbeat']
    combstomask['1REST_8BEATS'] = not parameters['oneresteightbeat']

    # 2 NOTES
    # 1 BEAT
    combstomask['EN_EN'] = not parameters['en_en']
    combstomask['ER_EN'] = not parameters['er_en']
    combstomask['EN_ER'] = not parameters['en_er']
    combstomask['DEN_SN'] = not parameters['den_sn']
    combstomask['SN_DEN'] = not parameters['sn_den']
    # 2 BEATS
    combstomask['DQN_EN'] = not parameters['dqn_en']
    combstomask['QR-ER_EN'] = not parameters['qr_er_en']
    combstomask['DQN_ER'] = not parameters['dqn_er']
    combstomask['EN_EN-QN'] = not parameters['en_en_qn']
    # 3 BEATS
    combstomask['QN-DQN_EN'] = not parameters['qn_dqn_en']
    combstomask['QR-QR-ER_EN'] = not parameters['qr_qr_er_en']
    combstomask['QN-DQN_ER'] = not parameters['qn_dqn_er']
    combstomask['EN_EN-HN'] = not parameters['en_en_hn']
    # 4 BEATS
    combstomask['HN-DQN_EN'] = not parameters['hn_dqn_en']
    combstomask['QR-QR-QR-ER_EN'] = not parameters['qr_qr_qr_er_en']
    combstomask['HN-DQN_ER'] = not parameters['hn_dqn_er']
    combstomask['EN_EN-DHN'] = not parameters['en_en_dhn']

    # 3 NOTES
    # 1 BEAT
    combstomask['EN_SN_SN'] = not parameters['en_sn_sn']
    combstomask['ER_SN_SN'] = not parameters['er_sn_sn']
    combstomask['SN_SN_EN'] = not parameters['sn_sn_en']
    combstomask['SN_SN_ER'] = not parameters['sn_sn_er']
    combstomask['SN_EN_SN'] = not parameters['sn_en_sn']
    combstomask['T_EN_EN_EN'] = not parameters['t_en_en_en']
    combstomask['T_EN_DEN_SN'] = not parameters['t_en_den_sn']
    combstomask['T_EN_SN_DEN'] = not parameters['t_en_sn_den']
    combstomask['T_SN_EN_DEN'] = not parameters['t_sn_en_den']
    combstomask['T_SN_DEN_EN'] = not parameters['t_sn_den_en']
    combstomask['T_DEN_EN_SN'] = not parameters['t_den_en_sn']
    combstomask['T_DEN_SN_EN'] = not parameters['t_den_sn_en']
    # 2 BEATS
    combstomask['EN_QN_EN'] = not parameters['en_qn_en']
    combstomask['DQN_SN_SN'] = not parameters['dqn_sn_sn']
    # 3 BEATS
    combstomask['QN-DQN_SN_SN'] = not parameters['qn_dqn_sn_sn']
    # 4 BEATS
    combstomask['HN-DQN_SN_SN'] = not parameters['hn_dqn_sn_sn']

    # 4 NOTES
    combstomask['SN_SN_SN_SN'] = not parameters['sn_sn_sn_sn']

    # Processing
    update_method(state='STARTED', meta={'progression': 0, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Loading analog score (previous step)", })
    DigPart = DigitalPartition()
    for k_note in range(0, len(type_b)):
        DigPart.AddNote(type_b[k_note], length_s[k_note], pitch_st[k_note])
    update_method(state='STARTED', meta={'progression': 1, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Minimizing height note errors", })
    DigPart.A_MinimizeHeightError()
    update_method(state='STARTED', meta={'progression': 2, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Searching for the best key", })
    DigPart.B_AutoSetFifths()
    update_method(state='STARTED', meta={'progression': 3, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Searching for the best clef to use", })
    DigPart.C_AutoSetClef()
    update_method(state='STARTED', meta={'progression': 4, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Searching for the best octave to use", })
    DigPart.D_AutoTranslateOctave()
    update_method(state='STARTED', meta={'progression': 5, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Searching best rythms configuration", })
    DigPart.E_GetConfigurationsForAllNotes()
    DigPart.F_MaskCOMBINATIONS(combstomask)
    DigPart.G_BuildGraph(errormax, delaymin_s, delaymax_s, maxdelayvar)
    DigPart.H_GetOptimalPath()
    DigPart.I_GetPathInfos()
    update_method(state='STARTED', meta={'progression': 6, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Creating midi score", })
    MidiString = DigPart.J_GenerateScore("midi")
    update_method(state='STARTED', meta={'progression': 7, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Creating midi score (without rythm detection)", })
    MidiString_norythm = DigPart.J_GenerateScore("midi_norythm")
    update_method(state='STARTED', meta={'progression': 8, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Creating musicxml score", })
    XMLString = DigPart.J_GenerateScore("musicxml", ProjectOwner, ProjectName)
    update_method(state='STARTED', meta={'progression': 9, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Saving files", })
    OUTPUT = {'MidiString': MidiString, 'MidiString_norythm': MidiString_norythm, 'XMLString': XMLString}
    # Checking if the ouput is correct
    check_rythmresults(OUTPUT)
    return(OUTPUT)


# PITCH

def UpdatePitchResults(id_project, parameters, results):
    # Get project instance
    instance_project = Project.objects.get(id=id_project)
    # Create Pitch Detection Results (WITHOUT SAVING)
    instance_pitchresults = PitchDetectionResult(project=instance_project)
    # Create Pitch Detection Parameters
    pitchserializer = PitchDetectionSerializer(data=parameters)
    pitchserializer.is_valid(raise_exception=True)
    # Set values of the pitch results
    instance_pitchresults.pitch_st = list(results[0]['pitch_st'])
    instance_pitchresults.energy_db = list(results[0]['energy_db'])
    instance_pitchresults.te_s = results[0]['te_s']
    instance_pitchresults.f0_hz = results[0]['f0_hz']
    instance_pitchresults.timestart_s = results[1]
    instance_pitchresults.timestop_s = results[2]
    # Save Pitch Results
    instance_pitchresults.save()
    pitchserializer.save(pitchdetectionresult=instance_pitchresults)


# STEP

def UpdateStepResults(id_project, parameters, results):
    # Get project instance
    instance_project = Project.objects.get(id=id_project)
    instance_pitchresult = instance_project.pitchdetectionresult
    # Create Pitch Detection Results (WITHOUT SAVING)
    instance_stepresults = StepDetectionResult(pitchdetectionresult=instance_pitchresult)
    # Create Pitch Detection Parameters
    stepserializer = StepDetectionSerializer(data=parameters)
    stepserializer.is_valid(raise_exception=True)
    # Set values of the pitch results
    instance_stepresults.type_b = list([results[0][k]['type_b'] for k in range(0, len(results[0]))])
    instance_stepresults.length_s = list([results[0][k]['length_s'] for k in range(0, len(results[0]))])
    instance_stepresults.f0_hz = list([results[0][k]['f0_hz'] for k in range(0, len(results[0]))])
    instance_stepresults.pitch_st = list([results[0][k]['pitch_st'] for k in range(0, len(results[0]))])
    instance_stepresults.energy_db = list([results[0][k]['energy_db'] for k in range(0, len(results[0]))])
    instance_stepresults.linked_b = list([results[0][k]['linked_b'] for k in range(0, len(results[0]))])
    instance_stepresults.offset_s = results[1]
    instance_stepresults.save()
    # Save Step Results
    instance_stepresults.save()
    stepserializer.save(stepdetectionresult=instance_stepresults)


# RYTHM

def UpdateRythmResults(id_project, parameters, results):
    # Get project instance
    instance_project = Project.objects.get(id=id_project)
    instance_pitchresult = instance_project.pitchdetectionresult
    instance_stepresult = instance_pitchresult.stepdetectionresult
    # Create Pitch Detection Results (WITHOUT SAVING)
    instance_rythmresults = RythmDetectionResult(stepdetectionresult=instance_stepresult)
    # Create Pitch Detection Parameters
    rythmserializer = RythmDetectionSerializer(data=parameters)
    rythmserializer.is_valid(raise_exception=True)
    # Set values of the pitch results
    instance_rythmresults.midifile.save("temp", ContentFile(results['MidiString']))
    instance_rythmresults.midifile_norythm.save("temp", ContentFile(results['MidiString_norythm']))
    instance_rythmresults.musicxmlfile.save("temp", ContentFile(results['XMLString']))
    instance_rythmresults.save()
    # Save Step Results
    instance_rythmresults.save()
    rythmserializer.save(rythmdetectionresult=instance_rythmresults)


@shared_task()
def rundirectconversion(project_id, projectpitchdetectionparam, projectstepdetectionparam, projectrythmdetectionparam):
    # Pitch detedction
    UpdateMethod = current_task.update_state
    pitch_result = runpitchdetection(project_id, projectpitchdetectionparam, update_method=UpdateMethod)
    UpdatePitchResults(project_id, projectpitchdetectionparam, pitch_result)

    # Step detection
    step_result = runstepdetection(project_id, projectstepdetectionparam, update_method=UpdateMethod)
    UpdateStepResults(project_id, projectstepdetectionparam, step_result)

    # Rythm detection
    rythm_result = runrythmdetection(project_id, projectrythmdetectionparam, update_method=UpdateMethod)
    UpdateRythmResults(project_id, projectrythmdetectionparam, rythm_result)


def deleteProjectProcess(task_id):
    projectprocess = ProjectProcess.objects.all().filter(task_id=task_id)
    if(projectprocess.exists()):
        projectprocess[0].delete()


@task_success.connect(sender=runpitchdetection)
def task_pitch_success_action(sender=None, headers=None, body=None, **kwargs):
    task_id = sender.request.id
    project_id = sender.request.args[0]
    parameters = sender.request.args[1]
    results = kwargs['result']
    UpdatePitchResults(project_id, parameters, results)
    deleteProjectProcess(task_id)


@task_success.connect(sender=runstepdetection)
def task_step_success_action(sender=None, headers=None, body=None, **kwargs):
    task_id = sender.request.id
    project_id = sender.request.args[0]
    parameters = sender.request.args[1]
    results = kwargs['result']
    UpdateStepResults(project_id, parameters, results)
    deleteProjectProcess(task_id)


@task_success.connect(sender=runrythmdetection)
def task_rythm_success_action(sender=None, headers=None, body=None, **kwargs):
    task_id = sender.request.id
    project_id = sender.request.args[0]
    parameters = sender.request.args[1]
    results = kwargs['result']
    UpdateRythmResults(project_id, parameters, results)
    deleteProjectProcess(task_id)


# DIRECT CONVERSION

@task_success.connect(sender=rundirectconversion)
def task_direct_success_action(sender=None, headers=None, body=None, **kwargs):
    task_id = sender.request.id
    # project_id = sender.request.args[0]
    # pitch_parameters = sender.request.args[1]
    # step_parameters = sender.request.args[2]
    # rythm_parameters = sender.request.args[3]
    # pitch_result = kwargs['result'][0]
    # step_result = kwargs['result'][1]
    # rythm_result = kwargs['result'][2]
    deleteProjectProcess(task_id)


@task_failure.connect(sender=runpitchdetection)
@task_failure.connect(sender=runstepdetection)
@task_failure.connect(sender=runrythmdetection)
@task_failure.connect(sender=rundirectconversion)
def task_failure_action(sender=None, headers=None, body=None, **kwargs):
    deleteProjectProcess(sender.request.id)


@task_revoked.connect(sender=runpitchdetection)
@task_revoked.connect(sender=runstepdetection)
@task_revoked.connect(sender=runrythmdetection)
@task_revoked.connect(sender=rundirectconversion)
def task_revoked_action(sender=None, headers=None, body=None, **kwargs):
    deleteProjectProcess(kwargs['request'].id)


@shared_task()
def runfreeconversion(audiofile, email, timestart_s=None, timestop_s=None):
    UpdateMethod = current_task.update_state

    # Pitch detedction
    temp_pitch_parameters = AbstractPitchDetectionParam()
    windowtimesize_s = temp_pitch_parameters.windowtimesize_s
    sonogramperiod_s = temp_pitch_parameters.sonogramperiod_s
    f0_hz = temp_pitch_parameters.f0_hz
    freqmin_hz = temp_pitch_parameters.freqmin_hz
    freqmax_hz = temp_pitch_parameters.freqmax_hz
    cutoff = temp_pitch_parameters.cutoff
    smallcutoff = temp_pitch_parameters.smallcutoff
    # Processing
    AUDIO = AudioWav(audiofile)
    AUDIO.A_DefineMcLeodParameters(freqmin_hz, freqmax_hz, cutoff, smallcutoff)
    OUTPUT_PITCH = AUDIO.B_ExtractSemitonegram(windowtimesize_s, sonogramperiod_s, f0_hz, timestart_s, timestop_s, UpdateMethod)
    # Checking if the ouput is correct
    check_pitchresults(OUTPUT_PITCH)

    # Step detection
    temp_step_parameters = AbstractStepDetectionParam()
    # Inputs
    pitch_st = list(OUTPUT_PITCH['pitch_st'])
    energy_db = list(OUTPUT_PITCH['energy_db'])
    te_s = OUTPUT_PITCH['te_s']
    f0_hz = OUTPUT_PITCH['f0_hz']
    # Parameters
    medianfiltersize_s = temp_step_parameters.medianfiltersize_s
    thresholdenergyon_db = temp_step_parameters.thresholdenergyon_db
    thresholdenergyoff_db = temp_step_parameters.thresholdenergyoff_db
    maxpitchvariation_st = temp_step_parameters.maxpitchvariation_st
    minimumtimesize_s = temp_step_parameters.minimumtimesize_s
    minnotesize_s = temp_step_parameters.minnotesize_s
    minnotediff_st = temp_step_parameters.minnotediff_st
    lmhgaussian_st = temp_step_parameters.lmhgaussian_st
    # Processing
    UpdateMethod(state='STARTED', meta={'progression': 0, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Loading pitch array", })
    SONO = Sonogram(pitch_st, energy_db, te_s, f0_hz)
    UpdateMethod(state='STARTED', meta={'progression': 1, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Applying median filter", })
    SONO.A_ApplyMedianFilter(medianfiltersize_s)
    UpdateMethod(state='STARTED', meta={'progression': 2, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Threshold on the energy", })
    SONO.B_Masked_AutoEnergy(thresholdenergyon_db, thresholdenergyoff_db)
    UpdateMethod(state='STARTED', meta={'progression': 3, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Maximum pitch variation", })
    SONO.C_Masked_MaximumVariation(maxpitchvariation_st)
    UpdateMethod(state='STARTED', meta={'progression': 4, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Filtering too short detections", })
    SONO.D_Masked_MinimumTimeSize(minimumtimesize_s)
    UpdateMethod(state='STARTED', meta={'progression': 5, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Detecting linked notes", })
    SONO.E_DetectGroupsOfNotes()
    UpdateMethod(state='STARTED', meta={'progression': 6, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Extracting notes", })
    SONO.F_Detectnotes(minnotesize_s, minnotediff_st, lmhgaussian_st)
    UpdateMethod(state='STARTED', meta={'progression': 7, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Generating output", })
    OUTPUT_STEP = SONO.G_GenerateAnalogPartition()
    UpdateMethod(state='STARTED', meta={'progression': 8, 'total': 8, 'mainstepname': "Step detection", 'substepname': "Saving output", })
    # Checking if the ouput is correct
    check_stepresults(OUTPUT_STEP)




    # Rythm detection
    temp_rythm_parameters = AbstractRythmDetectionParam()
    # Inputs
    type_b = list([OUTPUT_STEP[k]['type_b'] for k in range(0, len(OUTPUT_STEP))])
    length_s = list([OUTPUT_STEP[k]['length_s'] for k in range(0, len(OUTPUT_STEP))])
    pitch_st = list([OUTPUT_STEP[k]['pitch_st'] for k in range(0, len(OUTPUT_STEP))])
    # Parameters
    delaymin_s = temp_rythm_parameters.delaymin_s
    delaymax_s = temp_rythm_parameters.delaymax_s
    maxdelayvar = temp_rythm_parameters.maxdelayvar
    errormax = temp_rythm_parameters.errormax
    combstomask = {}
    combstomask['1NOTE_1BEAT'] = not temp_rythm_parameters.onenoteonebeat
    combstomask['1NOTE_2BEATS'] = not temp_rythm_parameters.onenotetwobeat
    combstomask['1NOTE_3BEATS'] = not temp_rythm_parameters.onenotethreebeat
    combstomask['1NOTE_4BEATS'] = not temp_rythm_parameters.onenotefourbeat
    combstomask['1NOTE_5BEATS'] = not temp_rythm_parameters.onenotefivebeat
    combstomask['1NOTE_6BEATS'] = not temp_rythm_parameters.onenotesixbeat
    combstomask['1NOTE_7BEATS'] = not temp_rythm_parameters.onenotesevenbeat
    combstomask['1NOTE_8BEATS'] = not temp_rythm_parameters.onenoteeightbeat
    combstomask['1REST_1BEAT'] = not temp_rythm_parameters.onerestonebeat
    combstomask['1REST_2BEATS'] = not temp_rythm_parameters.oneresttwobeat
    combstomask['1REST_3BEATS'] = not temp_rythm_parameters.onerestthreebeat
    combstomask['1REST_4BEATS'] = not temp_rythm_parameters.onerestfourbeat
    combstomask['1REST_5BEATS'] = not temp_rythm_parameters.onerestfivebeat
    combstomask['1REST_6BEATS'] = not temp_rythm_parameters.onerestsixbeat
    combstomask['1REST_7BEATS'] = not temp_rythm_parameters.onerestsevenbeat
    combstomask['1REST_8BEATS'] = not temp_rythm_parameters.oneresteightbeat

    # 2 NOTES
    # 1 BEAT
    combstomask['EN_EN'] = not temp_rythm_parameters.en_en
    combstomask['ER_EN'] = not temp_rythm_parameters.er_en
    combstomask['EN_ER'] = not temp_rythm_parameters.en_er
    combstomask['DEN_SN'] = not temp_rythm_parameters.den_sn
    combstomask['SN_DEN'] = not temp_rythm_parameters.sn_den
    # 2 BEATS
    combstomask['DQN_EN'] = not temp_rythm_parameters.dqn_en
    combstomask['QR-ER_EN'] = not temp_rythm_parameters.qr_er_en
    combstomask['DQN_ER'] = not temp_rythm_parameters.dqn_er
    combstomask['EN_EN-QN'] = not temp_rythm_parameters.en_en_qn
    # 3 BEATS
    combstomask['QN-DQN_EN'] = not temp_rythm_parameters.qn_dqn_en
    combstomask['QR-QR-ER_EN'] = not temp_rythm_parameters.qr_qr_er_en
    combstomask['QN-DQN_ER'] = not temp_rythm_parameters.qn_dqn_er
    combstomask['EN_EN-HN'] = not temp_rythm_parameters.en_en_hn
    # 4 BEATS
    combstomask['HN-DQN_EN'] = not temp_rythm_parameters.hn_dqn_en
    combstomask['QR-QR-QR-ER_EN'] = not temp_rythm_parameters.qr_qr_qr_er_en
    combstomask['HN-DQN_ER'] = not temp_rythm_parameters.hn_dqn_er
    combstomask['EN_EN-DHN'] = not temp_rythm_parameters.en_en_dhn

    # 3 NOTES
    # 1 BEAT
    combstomask['EN_SN_SN'] = not temp_rythm_parameters.en_sn_sn
    combstomask['ER_SN_SN'] = not temp_rythm_parameters.er_sn_sn
    combstomask['SN_SN_EN'] = not temp_rythm_parameters.sn_sn_en
    combstomask['SN_SN_ER'] = not temp_rythm_parameters.sn_sn_er
    combstomask['SN_EN_SN'] = not temp_rythm_parameters.sn_en_sn
    combstomask['T_EN_EN_EN'] = not temp_rythm_parameters.t_en_en_en
    combstomask['T_EN_DEN_SN'] = not temp_rythm_parameters.t_en_den_sn
    combstomask['T_EN_SN_DEN'] = not temp_rythm_parameters.t_en_sn_den
    combstomask['T_SN_EN_DEN'] = not temp_rythm_parameters.t_sn_en_den
    combstomask['T_SN_DEN_EN'] = not temp_rythm_parameters.t_sn_den_en
    combstomask['T_DEN_EN_SN'] = not temp_rythm_parameters.t_den_en_sn
    combstomask['T_DEN_SN_EN'] = not temp_rythm_parameters.t_den_sn_en
    # 2 BEATS
    combstomask['EN_QN_EN'] = not temp_rythm_parameters.en_qn_en
    combstomask['DQN_SN_SN'] = not temp_rythm_parameters.dqn_sn_sn
    # 3 BEATS
    combstomask['QN-DQN_SN_SN'] = not temp_rythm_parameters.qn_dqn_sn_sn
    # 4 BEATS
    combstomask['HN-DQN_SN_SN'] = not temp_rythm_parameters.hn_dqn_sn_sn

    # 4 NOTES
    combstomask['SN_SN_SN_SN'] = not temp_rythm_parameters.sn_sn_sn_sn

    # Processing
    UpdateMethod(state='STARTED', meta={'progression': 0, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Loading analog score (previous step)", })
    DigPart = DigitalPartition()
    for k_note in range(0, len(type_b)):
        DigPart.AddNote(type_b[k_note], length_s[k_note], pitch_st[k_note])
    UpdateMethod(state='STARTED', meta={'progression': 1, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Minimizing height note errors", })
    DigPart.A_MinimizeHeightError()
    UpdateMethod(state='STARTED', meta={'progression': 2, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Searching for the best key", })
    DigPart.B_AutoSetFifths()
    UpdateMethod(state='STARTED', meta={'progression': 3, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Searching for the best clef to use", })
    DigPart.C_AutoSetClef()
    UpdateMethod(state='STARTED', meta={'progression': 4, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Searching for the best octave to use", })
    DigPart.D_AutoTranslateOctave()
    UpdateMethod(state='STARTED', meta={'progression': 5, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Searching best rythms configuration", })
    DigPart.E_GetConfigurationsForAllNotes()
    DigPart.F_MaskCOMBINATIONS(combstomask)
    DigPart.G_BuildGraph(errormax, delaymin_s, delaymax_s, maxdelayvar)
    DigPart.H_GetOptimalPath()
    DigPart.I_GetPathInfos()
    UpdateMethod(state='STARTED', meta={'progression': 6, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Creating midi score", })
    MidiString = DigPart.J_GenerateScore("midi")
    UpdateMethod(state='STARTED', meta={'progression': 7, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Creating midi score (without rythm detection)", })
    MidiString_norythm = DigPart.J_GenerateScore("midi_norythm")
    UpdateMethod(state='STARTED', meta={'progression': 8, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Creating musicxml score", })
    XMLString = DigPart.J_GenerateScore("musicxml", author="scorelisto.com", title="Untitled")
    UpdateMethod(state='STARTED', meta={'progression': 9, 'total': 9, 'mainstepname': "Rythm detection", 'substepname': "Saving files", })
    OUTPUT_RYTHM = {'MidiString': MidiString, 'MidiString_norythm': MidiString_norythm, 'XMLString': XMLString}
    # Checking if the ouput is correct
    check_rythmresults(OUTPUT_RYTHM)
    return(XMLString, MidiString, MidiString_norythm, OUTPUT_PITCH)


def SendEmailFreeConversionSuccess(to_email, XMLString):
    mail_subject = '[scorelisto.com] Your scores !'
    # current_site = get_current_site(request)
    message = render_to_string('email-freeconversion-success.html', {})
    msg = EmailMultiAlternatives(mail_subject, message, settings.EMAIL_HOST_USER, [to_email])
    msg.attach('score.xml', XMLString, 'text/xml')
    msg.send()


def SendEmailFreeConversionError(to_email):
    mail_subject = '[scorelisto.com] Error !'
    # current_site = get_current_site(request)
    message = render_to_string('email-freeconversion-error.html', {})
    send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [to_email])


def SendEmailSupportFreeConversionSuccess(to_email, XMLString, audiopath):
    mail_subject = '[scorelisto.com] Someone Use the free converter: success'
    # current_site = get_current_site(request)
    message = render_to_string('email-support-freeconversion-success.html', {
        'file': audiopath,
    })
    msg = EmailMultiAlternatives(mail_subject, message, settings.EMAIL_HOST_USER, [to_email])
    msg.attach('score.xml', XMLString, 'text/xml')
    msg.send()


def SendEmailSupportFreeConversionError(to_email, audiopath):
    mail_subject = '[scorelisto.com] Someone used the free converter: failed'
    # current_site = get_current_site(request)
    message = render_to_string('email-support-freeconversion-error.html', {
        'file': audiopath,
    })
    send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [to_email])


@task_success.connect(sender=runfreeconversion)
def task_free_success_action(sender=None, headers=None, body=None, **kwargs):
    # task_id = sender.request.id
    audiofile = sender.request.args[0]
    email = sender.request.args[1]
    XMLString = kwargs['result'][0]
    # MidiString = kwargs['result'][1]
    # MidiString_norythm = kwargs['result'][2]
    # PITCH = kwargs['result'][2]
    SendEmailFreeConversionSuccess(email, XMLString)
    SendEmailSupportFreeConversionSuccess("support@scorelisto.com", XMLString, audiofile)


@task_failure.connect(sender=runfreeconversion)
def task_free_failure_action(sender=None, headers=None, body=None, **kwargs):
    audiofile = sender.request.args[0]
    email = sender.request.args[1]
    SendEmailFreeConversionError(email)
    SendEmailSupportFreeConversionError("support@scorelisto.com", audiofile)
