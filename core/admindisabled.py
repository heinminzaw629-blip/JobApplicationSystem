from django.contrib import admin
from django.utils import timezone
from django.contrib.auth.models import Group
from django.db import models

from .models import Company, CompanyUser, Application, AppFile


# -------- Hide Group --------
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


# -------- AppFile Inline --------
class AppFileInline(admin.TabularInline):
    model = AppFile
    extra = 0
    fields = ("kind", "file")


# -------- Application Admin --------
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

    # ✅ Review note အတွက် hint + textarea size
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

    # ✅ Status ပြောင်းတဲ့အချိန် timestamp auto
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


# -------- Company --------
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


# -------- CompanyUser --------
@admin.register(CompanyUser)
class CompanyUserAdmin(admin.ModelAdmin):
    # ✅ အရေးကြီး: user ကိုပါ ပြမယ် (login user နဲ့ ချိတ်ဖို့)
    list_display = (
        "id",
        "username",
        "user",              # ✅ NEW
        "company",
        "email",
        "phone",
        "postal_code",
        "approved_by",
        "download_allowed_at",
    )

    search_fields = ( "user__username", "email", "phone", "company__name")  # ✅ user__username NEW
    list_filter = ("company", "approved_by")

    # ✅ user field ကို edit/add page မှာပါ ထည့်ပေး
    fields = (
        "company",
        "user",              # ✅ NEW (ဒီဟာမရှိရင် 404 ပြန်တက်နိုင်)
        #"username",
        "email",
        "phone",
        "address",
        "postal_code",
        "approved_by",
        "download_allowed_at",
    )

    readonly_fields = ("download_allowed_at",)

    # ✅ approved_by ထည့်ပြီး save လုပ်တာနဲ့ download_allowed_at ကို auto-fill
    def save_model(self, request, obj, form, change):
        if obj.approved_by and not obj.download_allowed_at:
            obj.download_allowed_at = timezone.now()

        if not obj.approved_by:
            obj.download_allowed_at = None

        super().save_model(request, obj, form, change) ဒီကုတ်ကြိးတစခုလု့းကို moment off////////////////////////////