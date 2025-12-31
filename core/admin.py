from django.contrib import admin
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.db import models

admin.site.site_header = "Job_Application_System"
admin.site.site_title = "Job_Application"
admin.site.index_title = "Site_Administration"


from .models import Company, CompanyUser, Application, AppFile


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

    # Remove the widgets that show groups/permissions
    filter_horizontal = ()
    filter_vertical = ()

    # Remove groups/user_permissions from edit form fieldsets
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),  # ✅ hide groups/user_permissions
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    # Remove groups/user_permissions from add-user form too
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
# Application Admin
# -------------------------------------------------
@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "applicant_name",
        "applicant_email",
        "status",
        "visa_type",
        "location",
        "created_at",
        "approved_at",
        "rejected_at",
        "need_fix_at",
    )

    list_filter = ("status", "visa_type", "location", "company")
    search_fields = ("applicant_name", "applicant_email")
    inlines = [AppFileInline]

    readonly_fields = (
        "created_at",
        "approved_at",
        "rejected_at",
        "need_fix_at",
    )

    fields = (
        "company",
        "applicant_name",
        "applicant_email",
        "phone",
        "position",
        "location",
        "visa_type",
        "status",
        "review_note",
        "created_at",
        "approved_at",
        "rejected_at",
        "need_fix_at",
    )

    # Review note hint + textarea size
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

    # Status change => set timestamps
    def save_model(self, request, obj, form, change):
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
        # "username",  # keep commented if you don't want to edit it
        "email",
        "phone",
        "address",
        "postal_code",
        "approved_by",
        "download_allowed_at",
    )

    readonly_fields = ("download_allowed_at",)

    def save_model(self, request, obj, form, change):
        if obj.approved_by and not obj.download_allowed_at:
            obj.download_allowed_at = timezone.now()

        if not obj.approved_by:
            obj.download_allowed_at = None

        super().save_model(request, obj, form, change)
