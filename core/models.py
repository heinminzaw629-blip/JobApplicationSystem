from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Company(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class CompanyUser(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    # existing (မဖျက်)
    username = models.CharField(max_length=150)

    # ✅ NEW: login အတွက် Django auth user နဲ့ ချိတ်
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="company_user",
    )

    # company contact info (မင်းလိုချင်တာ)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_company_users",
    )

    download_allowed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username


class Application(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_NEED_FIX = "need_fix"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_NEED_FIX, "Need Fix"),
    ]

    VISA_CHOICES = [
        ("work_visa", "Work Visa"),
        ("tokuteigino", "Tokutei Ginou"),
        ("building_cleaning", "Building Cleaning"),
        ("restaurant", "Restaurant"),
        ("hotel_reception", "Hotel Reception"),
        ("kaigo", "Kaigo"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)

    applicant_name = models.CharField(max_length=200)
    applicant_email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    position = models.CharField(max_length=200, blank=True)

    location = models.CharField(max_length=200)
    visa_type = models.CharField(max_length=50, choices=VISA_CHOICES)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    need_fix_at = models.DateTimeField(null=True, blank=True)

    review_note = models.TextField(blank=True, max_length=3000)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.applicant_name


class AppFile(models.Model):
    KIND_CV = "cv"
    KIND_WORK = "work"
    KIND_VIDEO = "video"

    KIND_CHOICES = [
        (KIND_CV, "Cv"),
        (KIND_WORK, "Work History"),
        (KIND_VIDEO, "Video"),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="files")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    file = models.FileField(upload_to="applications/")

    def __str__(self):
        return f"{self.application} - {self.kind}"

#class EmailLog(models.Model):
   # application = models.ForeignKey("Application", on_delete=models.CASCADE)
   # event_key = models.CharField(max_length=120)
   # created_at = models.DateTimeField(auto_now_add=True)

    #class Meta:
     #   unique_together = ("application", "event_key")
