from django import forms

class ApplicationForm(forms.Form):
    company_id = forms.CharField(required=True)

    applicant_name = forms.CharField(max_length=200)
    applicant_email = forms.EmailField()
    phone = forms.CharField(max_length=50, required=False)
    position = forms.CharField(max_length=200, required=False)
    country = forms.CharField(required=True)
    location = forms.CharField(max_length=200)

    # 👇 UI dropdown ကနေ လာမယ့် data
    visa = forms.CharField(required=True)
    category = forms.CharField(required=True)

    # 👇 backend သုံးမယ့် field
    visa_type = forms.CharField(required=False)

    cv = forms.FileField()
    work_history = forms.FileField(required=False)
    video = forms.FileField()

    def clean(self):
        cleaned = super().clean()
        v = cleaned.get("visa")
        c = cleaned.get("category")
        if v and c:
            cleaned["visa_type"] = f"v:{v};c:{c}"
        return cleaned


