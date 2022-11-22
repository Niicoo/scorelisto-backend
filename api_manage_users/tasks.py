from __future__ import absolute_import, unicode_literals
from oauth2_provider.models import AccessToken
from oauth2_provider.models import RefreshToken
from be_django_rest_api.celery import app

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings


@app.task
def deleteExpiredTokens():
    for AT in AccessToken.objects.all():
        if(AT.is_expired()):
            AT.delete()
    for RT in RefreshToken.objects.all():
        if(RT.access_token is None):
            RT.delete()


def SendEmailAccountToDelete(userlist):
    NbUsersToDelete = len(userlist)
    mail_subject = 'ScoreListo - %d ACCOUNT(S) TO DELETE' % NbUsersToDelete
    to_email = settings.EMAIL_HOST_USER

    stringemail = ''
    for user in userlist:
        stringemail += '%s [%s]\n' % (user.username, user.email)

    message = render_to_string('email-delete-account-support.html', {'userlist': stringemail, })
    send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [to_email])


@app.task
def sendEmailAccountsToDelete():
    NbHoursToWait = settings.DELETE_ACCOUNT_DATA_HOURS
    DateNowMinusDelta = timezone.now() - timedelta(hours=NbHoursToWait)
    listusertodelete = []
    for user in User.objects.all():
        if((not user.is_active) and user.profile.is_deleted):
            if(user.profile.deletion_date < DateNowMinusDelta):
                listusertodelete.append(user)

    if(listusertodelete != []):
        SendEmailAccountToDelete(listusertodelete)


@app.task
def refreshRemainingProjects():
    for user in User.objects.all():
        if(user.profile.is_premium):
            MaxP = settings.PREMIUM_MAX_PROJECT_PER_DAY
        else:
            MaxP = settings.FREE_MAX_PROJECT_PER_DAY
        if(user.profile.projects_remaining < MaxP):
            user.profile.projects_remaining = MaxP
            user.profile.save()


app.conf.beat_schedule = {
    'delete-tokens-every-week': {
        'task': 'api_manage_users.tasks.deleteExpiredTokens',
        'schedule': 604800.0,
        'args': ()
    },
    'send-email-accounts-to-delete-every-eight-hour': {
        'task': 'api_manage_users.tasks.sendEmailAccountsToDelete',
        'schedule': 28800.0,
        'args': ()
    },
    'refresh-projects-every-twelve-hour': {
        'task': 'api_manage_users.tasks.refreshRemainingProjects',
        'schedule': 43200.0,
        'args': ()
    },
}
