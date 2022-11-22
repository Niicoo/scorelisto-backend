from django.urls import re_path
from rest_framework.urlpatterns import format_suffix_patterns
from api_manage_users.views import UserGetToken
from api_manage_users.views import UserCreate
from api_manage_users.views import UserDelete
from api_manage_users.views import UserActivate
from api_manage_users.views import UserUpdatePassword
from api_manage_users.views import UserResetPassword
from api_manage_users.views import UserSetNewPassword
from api_manage_users.views import UserReSendActivationEmail
from api_manage_users.views import UserRestore
from api_manage_users.views import UserCheckEmailAvailability
from api_manage_users.views import UserCheckUsernameAvailability
from api_manage_users.views import UserContact
from api_manage_users.views import UserQuotas
from api_manage_users.views import UserUsernameEmail

import oauth2_provider.views as oauth2_views

email_regex = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
username_regex = r'[a-zA-Z0-9_.+-]+'

urlpatterns = {
    # Contact
    re_path(r'^user\/contact\/?$', UserContact.as_view(), name="contact"),
    # Authentication
    re_path(r'^user\/authentication\/token\/?$', UserGetToken.as_view(), name="token"),
    re_path(r'^user\/authentication\/revoke-token\/?$', oauth2_views.RevokeTokenView.as_view(), name="revoke-token"),
    # Manage profile
    re_path(r'^user\/register\/?$', UserCreate.as_view(), name='register'),
    re_path(r'^user\/register\/retry\/?$', UserReSendActivationEmail.as_view(), name='retry'),
    re_path(r'^user\/activate\/?$', UserActivate.as_view(), name='activate'),
    re_path(r'^user\/update_password\/?$', UserUpdatePassword.as_view(), name='update_password'),
    re_path(r'^user\/reset_password\/?$', UserResetPassword.as_view(), name='reset_password'),
    re_path(r'^user\/set_new_password\/?$', UserSetNewPassword.as_view(), name='set_new_password'),
    re_path(r'^user\/delete\/?$', UserDelete.as_view(), name='delete'),
    re_path(r'^user\/restore\/?$', UserRestore.as_view(), name='restore'),
    re_path(r'^user\/quotas\/?$', UserQuotas.as_view(), name='quotas'),
    re_path(r'^user\/infos\/?$', UserUsernameEmail.as_view(), name='userinfos'),
    re_path(r'^user\/check_email_availability\/(?P<email>' + email_regex + r')\/?$', UserCheckEmailAvailability.as_view(), name='check_email_availability'),
    re_path(r'^user\/check_username_availability\/(?P<username>' + username_regex + r')\/?$', UserCheckUsernameAvailability.as_view(), name='check_username_availability'),
}

urlpatterns = format_suffix_patterns(urlpatterns)
