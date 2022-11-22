from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import os


def get_size(start_path='.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return(total_size)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # If the account is premium
    is_premium = models.BooleanField(default=False)
    # When the account is deleted
    is_deleted = models.BooleanField(default=False)
    deletion_date = models.DateTimeField(null=True, blank=True)
    # For limiting the number of project created per day
    projects_remaining = models.IntegerField(default=settings.FREE_MAX_PROJECT_PER_DAY)

    def get_projects_remaining_today(self):
        return(self.projects_remaining)

    def get_max_projects_per_day(self):
        if(self.is_premium):
            return(settings.PREMIUM_MAX_PROJECT_PER_DAY)
        else:
            return(settings.FREE_MAX_PROJECT_PER_DAY)

    def get_max_memory_allowed(self):
        if(self.is_premium):
            return(settings.PREMIUM_MAX_MEMORY_USED)
        else:
            return(settings.FREE_MAX_MEMORY_USED)

    def user_folder_path(self):
        UserFolderName = 'user_{0}'.format(self.user.pk)
        UserFullPath = os.path.join(settings.MEDIA_ROOT, UserFolderName)
        return(UserFullPath)

    def get_user_memory_used(self):
        UserPath = self.user_folder_path()
        if os.path.exists(UserPath):
            total_size = get_size(UserPath)
            return(total_size)
        else:
            return(0)

    def get_user_memory_remaining(self):
        MaxMemory = self.get_max_memory_allowed()
        MemoryUsed = self.get_user_memory_used()
        return(MaxMemory - MemoryUsed)


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
