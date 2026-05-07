from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin):
    """Base mixin that checks user role."""
    required_roles = ()

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if hasattr(request, 'user') and request.user.is_authenticated:
            if self.required_roles and request.user.role not in self.required_roles:
                raise PermissionDenied
        return response


class AdminRequiredMixin(RoleRequiredMixin):
    required_roles = ('admin',)


class MechanicRequiredMixin(RoleRequiredMixin):
    required_roles = ('mechanic',)


class StaffRequiredMixin(RoleRequiredMixin):
    required_roles = ('admin', 'mechanic')


class ClientRequiredMixin(RoleRequiredMixin):
    required_roles = ('client',)
