from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, FileResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .forms import ApplicationForm
from .models import Company, CompanyUser, Application, AppFile


# -------------------------
# Applicant Apply
# -------------------------
def apply_view(request):
    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            #company_id = form.cleaned_data.get("company_id")
            #company = Company.objects.filter(id=company_id).first() if company_id else None
            company_name = (form.cleaned_data.get("company_id") or "").strip()
            company = Company.objects.filter(name__iexact=company_name).first() if company_name else None

            app = Application.objects.create(
                company=company,
                applicant_name=form.cleaned_data["applicant_name"],
                applicant_email=form.cleaned_data["applicant_email"],
                phone=form.cleaned_data.get("phone", ""),
                position=form.cleaned_data.get("position", ""),
                country=form.cleaned_data.get("country", ""),  # ✅ add this
                location=form.cleaned_data["location"],
                visa_type=form.cleaned_data["visa_type"],
                status=Application.STATUS_PENDING,
                category=form.cleaned_data["category"],#add this

            )

            def save_file(kind, f):
                if f:
                    AppFile.objects.create(application=app, kind=kind, file=f)

            save_file(AppFile.KIND_CV, form.cleaned_data.get("cv"))
            save_file(AppFile.KIND_WORK, form.cleaned_data.get("work_history"))
            save_file(AppFile.KIND_VIDEO, form.cleaned_data.get("video"))

            messages.success(request, "Application submitted successfully.")
            return redirect("apply")

        messages.error(request, "Please correct the errors below.")
    else:
        form = ApplicationForm()

    return render(request, "core/apply.html", {"form": form})


# -------------------------
# Company Login / Logout
# -------------------------
def company_login_view(request):
    error = None
    if request.method == "POST":
        print("POST:", request.POST)  # ✅ ဒီလိုင်းထည့်////////////////////////////////////////////////////////////////
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        print("username:", username)  # ✅ ဒီလိုင်းထည့်////////////////////////////////////////////////////////////////
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("company_apps")

        error = "Login failed"

    return render(request, "core/company_login.html", {"error": error})


@login_required
def company_logout_view(request):
    logout(request)
    return redirect("company_login")


# -------------------------
# Company Approved Applications
# -------------------------
@login_required
def company_applications_view(request):
    cu = get_object_or_404(CompanyUser, user=request.user)

    # Approved applications only
    apps = Application.objects.filter(
        company=cu.company,
        status=Application.STATUS_APPROVED,
    ).order_by("-created_at")

    return render(request, "core/company_apps.html", {"apps": apps, "cu": cu})


# -------------------------
# Company Download file
# -------------------------
@login_required
def company_download_file(request, file_id: int):
    cu = get_object_or_404(CompanyUser, user=request.user)
    f = get_object_or_404(AppFile, id=file_id)

    # security check: company must match + application must be approved
    if f.application.company_id != cu.company_id:
        return HttpResponseForbidden("Forbidden")
    if f.application.status != Application.STATUS_APPROVED:
        return HttpResponseForbidden("Not approved")

    return FileResponse(f.file.open("rb"), as_attachment=True, filename=f.file.name)

    #return render(request, "core/apply.html", {"form": form, "companies": companies})
    #ompanies = Company.objects.all().order_by("name")  # name field မဟုတ်ရင်ပြောင်း
    return render(request, "core/apply.html", {"form": form, "companies": companies})



