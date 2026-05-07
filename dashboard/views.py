import json
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum, Count, Avg, Q, F
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from accounts.mixins import StaffRequiredMixin, AdminRequiredMixin
from accounts.models import User
from orders.models import WorkOrder
from services.models import SparePart


class DashboardView(StaffRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        month_start = today.replace(day=1)
        prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

        # ── KPI ───────────────────────────────────────────────

        active_statuses = ['new', 'diagnostics', 'approved', 'in_progress', 'waiting_parts', 'completed', 'ready']

        ctx['active_orders_count'] = WorkOrder.objects.filter(
            status__in=active_statuses
        ).count()

        ctx['today_revenue'] = WorkOrder.objects.filter(
            status='delivered', delivered_at__date=today,
        ).aggregate(t=Sum('final_cost'))['t'] or Decimal('0')

        ctx['month_revenue'] = WorkOrder.objects.filter(
            status='delivered', delivered_at__date__gte=month_start,
        ).aggregate(t=Sum('final_cost'))['t'] or Decimal('0')

        ctx['avg_check'] = WorkOrder.objects.filter(
            status='delivered', delivered_at__date__gte=month_start,
        ).aggregate(a=Avg('final_cost'))['a'] or Decimal('0')

        # Previous month for comparison
        prev_month_revenue = WorkOrder.objects.filter(
            status='delivered',
            delivered_at__date__gte=prev_month_start,
            delivered_at__date__lt=month_start,
        ).aggregate(t=Sum('final_cost'))['t'] or Decimal('0')

        if prev_month_revenue > 0:
            ctx['revenue_change'] = round(
                (float(ctx['month_revenue']) - float(prev_month_revenue))
                / float(prev_month_revenue) * 100
            )
        else:
            ctx['revenue_change'] = 0

        # ── Charts ────────────────────────────────────────────

        # Revenue last 7 days
        last_7 = [today - timedelta(days=i) for i in range(6, -1, -1)]
        revenue_data = []
        for day in last_7:
            r = WorkOrder.objects.filter(
                status='delivered', delivered_at__date=day,
            ).aggregate(t=Sum('final_cost'))['t'] or 0
            revenue_data.append({'date': day.strftime('%d.%m'), 'revenue': float(r)})
        ctx['revenue_chart_data'] = json.dumps(revenue_data)

        # Status distribution
        status_data = list(
            WorkOrder.objects
            .exclude(status__in=['delivered', 'cancelled'])
            .values('status')
            .annotate(count=Count('id'))
        )
        ctx['status_chart_data'] = json.dumps(status_data)

        # Orders trend 30 days
        trend_data = []
        for i in range(29, -1, -1):
            day = today - timedelta(days=i)
            cnt = WorkOrder.objects.filter(created_at__date=day).count()
            trend_data.append({'date': day.strftime('%d.%m'), 'count': cnt})
        ctx['trend_chart_data'] = json.dumps(trend_data)

        # Mechanic workload
        mechanic_data = list(
            User.objects.filter(role='mechanic', is_active=True).annotate(
                active_count=Count(
                    'assigned_orders',
                    filter=Q(assigned_orders__status__in=['in_progress', 'diagnostics', 'new']),
                )
            ).values('first_name', 'last_name', 'active_count')
        )
        ctx['mechanic_chart_data'] = json.dumps(mechanic_data)

        # Status labels for doughnut chart
        ctx['status_labels'] = json.dumps(dict(WorkOrder.Status.choices))

        # ── Tables ────────────────────────────────────────────

        ctx['recent_orders'] = (
            WorkOrder.objects
            .select_related('client', 'vehicle', 'assigned_mechanic')
            .order_by('-created_at')[:10]
        )

        ctx['low_stock_parts'] = SparePart.objects.filter(
            quantity_in_stock__lte=F('min_stock_level'),
            is_active=True,
        )

        # Today expected
        ctx['today_expected'] = (
            WorkOrder.objects
            .filter(estimated_completion__date=today)
            .exclude(status__in=['delivered', 'cancelled'])
            .select_related('client', 'vehicle')
        )

        return ctx


class DashboardKPIView(StaffRequiredMixin, View):
    """AJAX endpoint for KPI auto-refresh."""

    def get(self, request):
        today = timezone.localdate()
        month_start = today.replace(day=1)
        active_statuses = ['new', 'diagnostics', 'approved', 'in_progress', 'waiting_parts', 'completed', 'ready']

        return JsonResponse({
            'active_orders_count': WorkOrder.objects.filter(status__in=active_statuses).count(),
            'today_revenue': float(
                WorkOrder.objects.filter(status='delivered', delivered_at__date=today)
                .aggregate(t=Sum('final_cost'))['t'] or 0
            ),
            'month_revenue': float(
                WorkOrder.objects.filter(status='delivered', delivered_at__date__gte=month_start)
                .aggregate(t=Sum('final_cost'))['t'] or 0
            ),
            'avg_check': float(
                WorkOrder.objects.filter(status='delivered', delivered_at__date__gte=month_start)
                .aggregate(a=Avg('final_cost'))['a'] or 0
            ),
        })
