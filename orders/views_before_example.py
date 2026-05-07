# ❌ БЫЛО: проверка роли вручную через if в каждом view

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404
from .models import WorkOrder


@login_required
def workorder_list(request):
    # Проверка роли вручную в каждом view
    if request.user.role not in ('admin', 'mechanic'):
        raise PermissionDenied

    if request.user.role == 'mechanic':
        orders = WorkOrder.objects.filter(assigned_mechanic=request.user)
    else:
        orders = WorkOrder.objects.all()

    return render(request, 'orders/workorder_list.html', {'orders': orders})


@login_required
def workorder_create(request):
    # Снова дублирование проверки роли
    if request.user.role != 'admin':
        raise PermissionDenied
    # ...
    return render(request, 'orders/workorder_create.html')


@login_required
def workorder_detail(request, pk):
    # И снова проверка...
    if request.user.role not in ('admin', 'mechanic'):
        raise PermissionDenied
    order = get_object_or_404(WorkOrder, pk=pk)
    return render(request, 'orders/workorder_detail.html', {'order': order})
