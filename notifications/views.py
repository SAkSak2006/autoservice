from django.views.generic import ListView

from accounts.mixins import AdminRequiredMixin
from .models import Notification


class NotificationListView(AdminRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 30

    def get_queryset(self):
        qs = Notification.objects.select_related('client', 'work_order')
        channel = self.request.GET.get('channel')
        if channel:
            qs = qs.filter(channel=channel)
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs
