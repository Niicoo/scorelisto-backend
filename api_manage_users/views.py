from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer

from api_manage_users.serializers import UserContactSerializer
from api_manage_users.serializers import UserCreateSerializer
from api_manage_users.serializers import UserUpdatePasswordSerializer
from api_manage_users.serializers import UserEmailSerializer
from api_manage_users.serializers import UserUsernameSerializer
from api_manage_users.serializers import UserSetNewPasswordSerializer
from api_manage_users.serializers import UserDeleteSerializer
from api_manage_users.serializers import UserActivateSerializer
from api_manage_users.tokens import account_activation_token
# from api_manage_users.permissions import IsOwnerOrReadOnly

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.models import User
# from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text

from oauth2_provider.models import AccessToken, RefreshToken

from django.conf import settings
from django.utils import timezone

import oauth2_provider.views as oauth2_views

import json


def SendEmailActivationLink(user):
    mail_subject = 'ScoreListo - Activation link'
    to_email = user.email
    # current_site = get_current_site(request)
    message = render_to_string('email-activation-link.html', {
        'user': user,
        'uidb64': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
        'token': account_activation_token.make_token(user=user),
    })
    send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [to_email])


def SendEmailToContactAdress(data, username=''):
    mail_subject = '[scorelisto.com] New message !'
    to_email = "contact@scorelisto.com"
    # current_site = get_current_site(request)
    message = render_to_string('email-contact.html', {
        'name': data['name'],
        'email': data['email'],
        'phone': data['phone'],
        'username': username,
        'body': data['body'],
    })
    send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [to_email])


class UserContact(APIView):
    """
    Send email to contact@scorelisto.com.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format='json'):
        serializer = UserContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if request.user.is_authenticated:
            SendEmailToContactAdress(serializer.data, request.user.username)
        else:
            SendEmailToContactAdress(serializer.data)
        return Response(status=status.HTTP_200_OK)


class UserGetToken(oauth2_views.TokenView):

    def post(self, request, *args, **kwargs):
        JSONrequest = json.loads(request.body)
        if 'username' not in JSONrequest:
            return super(UserGetToken, self).post(request, *args, **kwargs)
        if '@' not in JSONrequest['username']:
            return super(UserGetToken, self).post(request, *args, **kwargs)
        TempUser = User.objects.filter(email=JSONrequest['username'])
        if TempUser.exists():
            JSONrequest['username'] = TempUser[0].username
            request._body = json.dumps(JSONrequest).encode('utf-8')
        return super(UserGetToken, self).post(request, *args, **kwargs)


class UserCreate(APIView):
    """
    Creates the user.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format='json'):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        SendEmailActivationLink(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserReSendActivationEmail(APIView):
    """
    Send Again the email activation link

    The email is sent only if:
        - the user exists
        - the user is not already active
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format='json'):
        serializer = UserEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if User.objects.filter(email=serializer.validated_data.get("email")).exists():
            user = User.objects.get(email=serializer.validated_data.get("email"))
            if not user.is_active:
                SendEmailActivationLink(user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserDelete(APIView):
    """
    Delete the user.
    """
    permission_classes = (permissions.IsAuthenticated, )

    def post(self, request, format='json'):
        user = self.request.user
        serializer = UserDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Check password
        password = serializer.validated_data.get("password")
        if not user.check_password(password):
            return Response({"password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
        # set_password also hashes the password that the user will get
        user.profile.is_deleted = True
        user.profile.deletion_date = timezone.now()
        user.is_active = False
        user.save()
        # Send a confirmation email
        mail_subject = 'ScoreListo - Account deleted'
        to_email = request.user.email
        # current_site = get_current_site(request)
        message = render_to_string('email-delete-account-confirmation.html', {'user': request.user, 'emailsupport': settings.EMAIL_HOST_USER})
        send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [to_email])
        AccessToken.objects.filter(user_id=user.id).delete()
        RefreshToken.objects.filter(user_id=user.id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserRestore(APIView):
    """
    Restore the user.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format='json'):
        serializer = UserEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if User.objects.filter(email=serializer.validated_data.get("email")).exists():
            user = User.objects.get(email=serializer.validated_data.get("email"))
            if((not user.is_active) and user.profile.is_deleted):
                user.profile.deletion_date = timezone.now()
                user.save()
                SendEmailActivationLink(user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserActivate(APIView):
    """
    Validate the user.
    """
    renderer_classes = (JSONRenderer, )
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format='json'):
        serializer = UserActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            uid = force_text(urlsafe_base64_decode(serializer.validated_data.get("uidb64")))
            user = User.objects.get(pk=uid)
            response_data = {'validation': 'success'}
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
            response_data = {'validation': 'fail'}

        if user is not None and account_activation_token.check_token(user, serializer.validated_data.get("token")):
            user.is_active = True
            user.profile.is_deleted = False
            user.save()
            response_data = {'validation': 'success'}
            # return redirect('home')
            return Response(response_data, status=status.HTTP_202_ACCEPTED)
        else:
            response_data = {'validation': 'fail'}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class UserUpdatePassword(APIView):
    """
    An endpoint for changing password.
    """
    permission_classes = (permissions.IsAuthenticated, )

    def get_object(self, queryset=None):
        return self.request.user

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = UserUpdatePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Check old password
        old_password = serializer.validated_data.get("old_password")
        if not self.object.check_password(old_password):
            return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
        # set_password also hashes the password that the user will get
        self.object.set_password(serializer.validated_data.get("new_password"))
        self.object.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserResetPassword(APIView):
    """
    Reset the user password.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format='json'):
        serializer = UserEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if User.objects.filter(email=serializer.validated_data.get("email")).exists():
            user = User.objects.get(email=serializer.validated_data.get("email"))
            mail_subject = "ScoreListo - Reset Password link"
            to_email = user.email
            message = render_to_string('email-reset-password-link.html', {
                'user': user,
                'uidb64': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token': PasswordResetTokenGenerator().make_token(user=user),
            })
            send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [to_email])
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserSetNewPassword(APIView):
    """
    Reset the user password.
    """
    renderer_classes = (JSONRenderer, )
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format='json'):
        serializer = UserSetNewPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            uid = force_text(urlsafe_base64_decode(serializer.validated_data.get("uidb64")))
            user = User.objects.get(pk=uid)
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if user is not None and PasswordResetTokenGenerator().check_token(user, serializer.validated_data.get("token")):
            user.set_password(serializer.validated_data.get("password"))
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class UserCheckEmailAvailability(APIView):
    """
    Check if an email is available.
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request, email):
        serializer = UserEmailSerializer(data={'email': email})
        serializer.is_valid(raise_exception=True)
        EmailAlreadyExists = not User.objects.filter(email=email).exists()
        return Response({'available': EmailAlreadyExists}, status=status.HTTP_200_OK)


class UserCheckUsernameAvailability(APIView):
    """
    Check if an username is available.
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request, username):
        serializer = UserUsernameSerializer(data={'username': username})
        serializer.is_valid(raise_exception=True)
        UsernameAlreadyExists = not User.objects.filter(username=username).exists()
        return Response({'available': UsernameAlreadyExists}, status=status.HTTP_200_OK)


class UserQuotas(APIView):
    """
    An endpoint for changing password.
    """
    permission_classes = (permissions.IsAuthenticated, )

    def get_object(self, queryset=None):
        return self.request.user

    def get(self, request):
        user = self.get_object()
        projects_max = user.profile.get_max_projects_per_day()
        projects_remaining = user.profile.get_projects_remaining_today()
        memory_max = user.profile.get_max_memory_allowed()
        memory_used = user.profile.get_user_memory_used()
        response_data = {'memory_max': memory_max, 'memory_used': memory_used, 'projects_max': projects_max, 'projects_remaining': projects_remaining, }
        return Response(response_data, status=status.HTTP_200_OK)


class UserUsernameEmail(APIView):
    """
    An endpoint for changing password.
    """
    permission_classes = (permissions.IsAuthenticated, )

    def get_object(self, queryset=None):
        return self.request.user

    def get(self, request):
        user = self.get_object()
        response_data = {'username': user.username, 'email': user.email, }
        return Response(response_data, status=status.HTTP_200_OK)
