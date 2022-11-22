from rest_framework import permissions
from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
import celery.result
from celery.task.control import revoke
from api_manage_projects.models import ProjectProcess
from api_manage_projects.serializers import CheckListTaskStateSerializer


class CheckTasksState(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = CheckListTaskStateSerializer

    def GetTaskState(self, task_id):
        task = celery.result.AsyncResult(task_id)
        progression = 0
        total = 0
        substepname = ""
        mainstepname = ""
        if(task.status == 'STARTED'):
            if('progression' in task.info):
                progression = task.info['progression']
            if('total' in task.info):
                total = task.info['total']
            if('substepname' in task.info):
                substepname = task.info['substepname']
            if('mainstepname' in task.info):
                mainstepname = task.info['mainstepname']
        response_data = {
            'status': task.status,
            'progression': progression,
            'total': total,
            'substepname': substepname,
            'mainstepname': mainstepname}
        return(response_data)

    def post(self, request):
        # Check if the parameters are ok
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print(serializer.data['task_ids'])
        # Get State for each tasks
        response_data = {}
        for task_id in serializer.data['task_ids']:
            response_data[task_id] = self.GetTaskState(task_id)
        return Response(response_data, status=status.HTTP_201_CREATED)


class RevokeTask(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, task_id):
        queryset_pp = ProjectProcess.objects.all()
        queryset_pp = queryset_pp.filter(owner=self.request.user)
        queryset_pp = queryset_pp.filter(task_id=task_id)
        if(queryset_pp.exists()):
            revoke(task_id, terminate=True)
            return(Response(status=status.HTTP_204_NO_CONTENT))
        else:
            response_data = {'task_id': 'Invalid task id or action not granted'}
            return(Response(response_data, status=status.HTTP_400_BAD_REQUEST))
