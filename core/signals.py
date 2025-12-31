from django.conf import settings
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.db import transaction
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import Application, CompanyUser, EmailLog


# ======================================================
# Helpers
# ======================================================

def get_admin_emails():
    return [email for _, email in getattr(settings, "ADMINS", [])]


def get_company_emails(app: Application) -> list[str]:
    emails = []

    # Company main email
    if getattr(app, "company_id", None) and getattr(app.company, "email", None):
        emails.append(app.company.email)

    # Company users emails
    if getattr(app, "company_id", None):
        qs = (
            CompanyUser.objects
            .filter(company_id=app.company_id)
            .exclude(email__isnull=True)
            .exclude(email="")
        )
        emails += list(qs.values_list("email", flat=True))

    return sorted(set([e.strip() for e in emails if e and e.strip()]))


def build_company_email_content(instance: Application):
    """
    Business-level email content
    Returns: subject, text_body, html_body
    """

    subject = f"New Job Application from Super Hotel Clean (ID #{instance.pk})"

    # Safe field access (no logic impact)
    applicant_name = getattr(instance, "applicant_name", getattr(instance, "name", ""))
    applicant_email = getattr(instance, "applicant_email", getattr(instance, "email", ""))
    applicant_phone = getattr(instance, "phone", getattr(instance, "phone_number", ""))
    position = getattr(instance, "position", getattr(instance, "job_title", ""))
    location = getattr(instance, "location", "")

    # --------------------------------------------------
    # Plain text (fallback)
    # --------------------------------------------------
    text_body = f"""
Dear Hiring Team,

We hope this email finds you well.

Super Hotel Clean has shared a job application with your company.
Please kindly review the application form at your convenience.
If the application is suitable, we would appreciate it if you could proceed with the next steps.

Application ID: {instance.pk}
Applicant Name: {applicant_name}
Applicant Email: {applicant_email}
Applicant Phone: {applicant_phone}
Position: {position}
Location: {location}

Should you require any additional information, please feel free to contact us.

Best regards,
Super Hotel Clean
Recruitment Team
""".strip()

    # --------------------------------------------------
    # HTML (Business-level design)
    # --------------------------------------------------
    html_body = f"""\
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
</head>
<body style="
  margin:0;
  padding:0;
  background-color:#f4f6f8;
  font-family:'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  color:#1f2933;
">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:24px;">
    <tr>
      <td align="center">

        <table width="600" cellpadding="0" cellspacing="0"
          style="
            background:#ffffff;
            border-radius:12px;
            padding:28px;
            box-shadow:0 6px 18px rgba(0,0,0,0.06);
          ">

          <tr>
            <td>

              <h2 style="
                margin:0 0 16px 0;
                font-size:22px;
                font-weight:600;
                color:#0f172a;
              ">
                New Job Application
              </h2>

              <p style="margin:0 0 12px 0; font-size:15px;">
                Dear Hiring Team,
              </p>

              <p style="margin:0 0 12px 0; font-size:15px;">
                We hope this email finds you well.
              </p>

              <p style="margin:0 0 12px 0; font-size:15px;">
                <strong>Super Hotel Clean</strong> has shared a job application with your company.
              </p>

              <p style="margin:0 0 18px 0; font-size:15px;">
                Please kindly review the application form at your convenience.
                If the application is suitable, we would appreciate it if you could proceed with the next steps.
              </p>

              <div style="
                background:#f8fafc;
                border:1px solid #e5e7eb;
                border-radius:8px;
                padding:14px;
                margin-bottom:18px;
              ">
                <p style="margin:0; font-size:14px;">
                  <strong>Application ID:</strong> {instance.pk}
                </p>
              </div>

              <table width="100%" cellpadding="0" cellspacing="0"
                style="border-collapse:collapse; margin-bottom:18px; font-size:14px;">
                <tr>
                  <td style="padding:10px; border:1px solid #e5e7eb; background:#f9fafb;"><strong>Applicant Name</strong></td>
                  <td style="padding:10px; border:1px solid #e5e7eb;">{applicant_name}</td>
                </tr>
                <tr>
                  <td style="padding:10px; border:1px solid #e5e7eb; background:#f9fafb;"><strong>Email</strong></td>
                  <td style="padding:10px; border:1px solid #e5e7eb;">{applicant_email}</td>
                </tr>
                <tr>
                  <td style="padding:10px; border:1px solid #e5e7eb; background:#f9fafb;"><strong>Phone</strong></td>
                  <td style="padding:10px; border:1px solid #e5e7eb;">{applicant_phone}</td>
                </tr>
                <tr>
                  <td style="padding:10px; border:1px solid #e5e7eb; background:#f9fafb;"><strong>Position</strong></td>
                  <td style="padding:10px; border:1px solid #e5e7eb;">{position}</td>
                </tr>
                <tr>
                  <td style="padding:10px; border:1px solid #e5e7eb; background:#f9fafb;"><strong>Location</strong></td>
                  <td style="padding:10px; border:1px solid #e5e7eb;">{location}</td>
                </tr>
              </table>

              <p style="margin:0 0 16px 0; font-size:15px;">
                Should you require any additional information, please feel free to contact us.
              </p>

              <hr style="border:none; border-top:1px solid #e5e7eb; margin:20px 0;">

              <p style="margin:0; font-size:14px; color:#475569;">
                Best regards,<br>
                <strong>Super Hotel Clean</strong><br>
                Recruitment Team
              </p>

            </td>
          </tr>
        </table>

        <p style="
          margin-top:14px;
          font-size:12px;
          color:#94a3b8;
        ">
          This is an automated email. Please do not reply.
        </p>

      </td>
    </tr>
  </table>
</body>
</html>
"""

    return subject, text_body, html_body


# ======================================================
# Signals (LOGIC UNCHANGED)
# ======================================================

@receiver(pre_save, sender=Application)
def application_pre_save(sender, instance: Application, **kwargs):
    if not instance.pk:
        instance._old_company_id = None
        return
    try:
        old = sender.objects.only("company_id").get(pk=instance.pk)
        instance._old_company_id = old.company_id
    except sender.DoesNotExist:
        instance._old_company_id = None


@receiver(post_save, sender=Application)
def notify_on_company_change(sender, instance: Application, created: bool, **kwargs):
    if created:
        return

    old_company_id = getattr(instance, "_old_company_id", None)
    new_company_id = getattr(instance, "company_id", None)

    if old_company_id == new_company_id:
        return

    if new_company_id is None:
        return

    event_key = f"company_change:{old_company_id}->{new_company_id}"

    try:
        with transaction.atomic():
            EmailLog.objects.create(application=instance, event_key=event_key)
    except Exception:
        return

    company_emails = get_company_emails(instance)
    admin_emails = get_admin_emails()

    # Company email
    if company_emails:
        subject, text_body, html_body = build_company_email_content(instance)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=company_emails,
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)

        # Admin confirm (unchanged logic)
        if admin_emails:
            EmailMessage(
                subject=f"[CONFIRM] Company emailed - Application #{instance.pk}",
                body=(
                    "Email sent to company.\n"
                    f"Application ID: {instance.pk}\n"
                    f"Recipients: {', '.join(company_emails)}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=admin_emails,
            ).send(fail_silently=True)


@receiver(post_save, sender=Application)
def notify_admin_on_application_submit(sender, instance: Application, created: bool, **kwargs):
    # ✅ Application submit/create ဖြစ်တဲ့အချိန်ပဲ
    if not created:
        return

    admin_emails = get_admin_emails()
    if not admin_emails:
        return

    # ✅ submit တစ်ခါ = mail တစ်ခါ (duplicate မဖြစ်အောင်)
    event_key = f"application_submitted:{instance.pk}"

    try:
        with transaction.atomic():
            EmailLog.objects.create(application=instance, event_key=event_key)
    except Exception:
        # already sent
        return

    # Safe fields
    applicant_name = getattr(instance, "applicant_name", getattr(instance, "name", ""))
    applicant_email = getattr(instance, "applicant_email", getattr(instance, "email", ""))
    applicant_phone = getattr(instance, "phone", getattr(instance, "phone_number", ""))
    position = getattr(instance, "position", getattr(instance, "job_title", ""))
    location = getattr(instance, "location", "")

    subject = f"[NEW] Application Submitted (ID #{instance.pk}) – Super Hotel Clean"

    body = f"""
Dear Admin Team,

A new job application has been successfully submitted to the system.
Please review the application at your earliest convenience.

Application Summary
- Application ID: #{instance.pk}

Applicant Details
- Name: {applicant_name}
- Email: {applicant_email}
- Phone: {applicant_phone}

Position Details
- Position: {position}
- Location: {location}

If any additional verification or follow-up is required, please proceed accordingly.

Best regards,
Super Hotel Clean
Recruitment System
(Automated Notification)
""".strip()

    EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=admin_emails,
    ).send(fail_silently=False)
