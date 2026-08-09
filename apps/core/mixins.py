from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles = []

    def test_func(self):
        return self.request.user.role in self.allowed_roles


class TenantQuerysetMixin:
    school_field = "school"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if getattr(user, "is_super_admin", False):
            return queryset

        school = getattr(user, "school", None)

        if not school:
            return queryset.none()

        return queryset.filter(**{self.school_field: school})