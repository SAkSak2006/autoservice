from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, UpdateView, TemplateView

from .forms import CustomUserCreationForm, CustomUserChangeForm, LoginForm


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Регистрация прошла успешно! Войдите в систему.')
        return response


class CustomLoginView(TemplateView):
    template_name = 'accounts/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self._get_redirect_url(request.user))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = kwargs.get('form', LoginForm())
        return ctx

    def post(self, request, *args, **kwargs):
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next') or self._get_redirect_url(user)
            return redirect(next_url)
        return self.render_to_response(self.get_context_data(form=form))

    @staticmethod
    def _get_redirect_url(user):
        if user.role == 'client':
            return '/portal/'
        return '/dashboard/'


class ProfileView(LoginRequiredMixin, UpdateView):
    form_class = CustomUserChangeForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Профиль обновлён.')
        return super().form_valid(form)


class CustomLogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, 'Вы вышли из системы.')
        return redirect('accounts:login')

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)
