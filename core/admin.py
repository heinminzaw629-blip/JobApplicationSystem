from django.contrib import admin
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.db import models
from django import forms
from django.core.exceptions import ValidationError

from .models import Company, CompanyUser, Application, AppFile

admin.site.site_header = "Job_Application_System"
admin.site.site_title = "Job_Application"
admin.site.index_title = "Site_Administration"


# -------------------------------------------------
# Hide Group from admin menu
# -------------------------------------------------
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


# -------------------------------------------------
# Hide "Groups" + "User permissions" fields on User admin UI
# (Does NOT delete permissions; only hides UI)
# -------------------------------------------------
User = get_user_model()

try:
    admin.site.unregister(User)  # unregister default User admin
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Keep Django's User admin but hide:
      - groups
      - user_permissions
    """

    filter_horizontal = ()
    filter_vertical = ()

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2"),
        }),
    )


# -------------------------------------------------
# AppFile Inline
# -------------------------------------------------
class AppFileInline(admin.TabularInline):
    model = AppFile
    extra = 0
    fields = ("kind", "file")


# -------------------------------------------------
# ✅ Application Admin Form (approved_by rule)
# -------------------------------------------------
class ApplicationAdminForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        # ✅ approved_by dropdown ထဲမှာ login user တစ်ယောက်ထဲပဲ ပြ
        if self.request and "approved_by" in self.fields:
            UserModel = get_user_model()
            field = self.fields["approved_by"]

            # dropdown = login user တစ်ယောက်ထဲ
            field.queryset = UserModel.objects.filter(pk=self.request.user.pk)

            # ✅ Approved by ဘေးက (+ ✏️ ❌ 👁) buttons ဖျက်
            field.widget.can_add_related = False
            field.widget.can_change_related = False
            field.widget.can_delete_related = False
            field.widget.can_view_related = False

    def clean(self):
        cleaned = super().clean()
        req = self.request
        status = cleaned.get("status")
        approved_by = cleaned.get("approved_by")

        if not req:
            return cleaned

        target_statuses = {
            Application.STATUS_APPROVED,
            Application.STATUS_REJECTED,
            Application.STATUS_NEED_FIX,
        }

        if status in target_statuses:
            if approved_by is None:
                raise ValidationError({"approved_by": "approved_by is required when status is changed."})

            if approved_by.pk != req.user.pk:
                raise ValidationError({"approved_by": "approved_by must be the currently logged-in user."})

        return cleaned


# -------------------------------------------------
# ✅ NEW: CompanyUser Admin Form (approved_by rule)
# -------------------------------------------------
class CompanyUserAdminForm(forms.ModelForm):
    class Meta:
        model = CompanyUser
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        # ✅ approved_by dropdown = current login user only
        if self.request and "approved_by" in self.fields:
            UserModel = get_user_model()
            field = self.fields["approved_by"]

            # dropdown = login user တစ်ယောက်ထဲ
            field.queryset = UserModel.objects.filter(pk=self.request.user.pk)

            # ✅ Approved by ဘေးက (+ ✏️ ❌ 👁) buttons ဖျက်
            field.widget.can_add_related = False
            field.widget.can_change_related = False
            field.widget.can_delete_related = False
            field.widget.can_view_related = False

    def clean(self):
        cleaned = super().clean()
        req = self.request
        approved_by = cleaned.get("approved_by")

        if not req:
            return cleaned

        # ✅ approved_by မရွေးရင် save မရ
        if approved_by is None:
            raise ValidationError({"approved_by": "approved_by is required."})

        # ✅ approved_by က login user မဟုတ်ရင် save မရ
        if approved_by.pk != req.user.pk:
            raise ValidationError({"approved_by": "approved_by must be the currently logged-in user."})

        return cleaned


# -------------------------------------------------
# Application Admin
# -------------------------------------------------
@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    form = ApplicationAdminForm

    list_display = (
        "id",
        "applicant_name",
        "applicant_email",
        "status",
        "visa_selected",
        "category",
        "location",
        "created_at",
        "approved_by",
        "approved_at",
        "rejected_at",
        "need_fix_at",
    )

    list_filter = ("status", "category", "location", "company")
    search_fields = ("applicant_name", "applicant_email", "visa_type", "category")
    inlines = [AppFileInline]

    readonly_fields = (
        "created_at",
        "approved_at",
        "rejected_at",
        "need_fix_at",
        "visa_selected",
    )

    fields = (
        "company",
        "applicant_name",
        "applicant_email",
        "phone",
        "position",
        "country",
        "location",
        "visa_selected",
        "category",
        "status",
        "approved_by",
        "review_note",
        "created_at",
        "approved_at",
        "rejected_at",
        "need_fix_at",
    )

    def get_form(self, request, obj=None, **kwargs):
        Form = super().get_form(request, obj, **kwargs)

        class RequestInjectedForm(Form):
            def __init__(self2, *args, **kw):
                kw["request"] = request
                super().__init__(*args, **kw)

        return RequestInjectedForm

    def visa_selected(self, obj):
        s = obj.visa_type or ""
        if s.startswith("v:") and ";c:" in s:
            visa = s.split(";c:")[0].replace("v:", "")
            LABELS = {
                "work_visa": "Work Visa",
                "tokuteigino": "Tokuteigino",
                "tokutei": "Tokutei",
                "kaigo": "Kaigo",
                "dependent": "Dependent",
                "student_visa": "Student Visa",
                "pr": "PR",
            }
            return LABELS.get(visa, visa)
        return s

    visa_selected.short_description = "Visa (Applicant Selected)"

    formfield_overrides = {
        models.TextField: {
            "widget": admin.widgets.AdminTextareaWidget(
                attrs={
                    "rows": 6,
                    "placeholder": "Write feedback for the applicant (up to 3000 characters)."
                }
            )
        }
    }

    def save_model(self, request, obj, form, change):
        target_statuses = {
            Application.STATUS_APPROVED,
            Application.STATUS_REJECTED,
            Application.STATUS_NEED_FIX,
        }

        if obj.status in target_statuses:
            if obj.approved_by is None:
                raise ValidationError("approved_by is required when status is changed.")
            if obj.approved_by_id != request.user.pk:
                raise ValidationError("approved_by must be the currently logged-in user.")

        if change and "status" in getattr(form, "changed_data", []):
            now = timezone.now()

            if obj.status == Application.STATUS_APPROVED and not obj.approved_at:
                obj.approved_at = now
            elif obj.status == Application.STATUS_REJECTED and not obj.rejected_at:
                obj.rejected_at = now
            elif obj.status == Application.STATUS_NEED_FIX and not obj.need_fix_at:
                obj.need_fix_at = now

        super().save_model(request, obj, form, change)


# -------------------------------------------------
# Company Admin
# -------------------------------------------------
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


# -------------------------------------------------
# CompanyUser Admin
# -------------------------------------------------
@admin.register(CompanyUser)
class CompanyUserAdmin(admin.ModelAdmin):
    form = CompanyUserAdminForm  # ✅ NEW

    list_display = (
        "id",
        "username",
        "user",
        "company",
        "email",
        "phone",
        "postal_code",
        "approved_by",
        "download_allowed_at",
    )

    search_fields = ("user__username", "email", "phone", "company__name")
    list_filter = ("company", "approved_by")

    fields = (
        "company",
        "user",
        # "username",
        "email",
        "phone",
        "address",
        "postal_code",
        "approved_by",
        "download_allowed_at",
    )

    readonly_fields = ("download_allowed_at",)

    # ✅ NEW: request ကို form ထဲ inject (CompanyUserAdminForm အတွက်)
    def get_form(self, request, obj=None, **kwargs):
        Form = super().get_form(request, obj, **kwargs)

        class RequestInjectedForm(Form):
            def __init__(self2, *args, **kw):
                kw["request"] = request
                super().__init__(*args, **kw)

        return RequestInjectedForm

    def save_model(self, request, obj, form, change):
        # ✅ မင်း original logic မဖျက်
        if obj.approved_by and not obj.download_allowed_at:
            obj.download_allowed_at = timezone.now()

        if not obj.approved_by:
            obj.download_allowed_at = None

        super().save_model(request, obj, form, change)
