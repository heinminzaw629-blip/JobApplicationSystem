from django import forms

VISA_CHOICES = [
    ("work_visa", "Work Visa"),
    ("tokuteigino", "Tokutei Ginou"),
    ("building_cleaning", "Building Cleaning"),
    ("restaurant", "Restaurant"),
    ("hotel_reception", "Hotel Reception"),
    ("kaigo", "Kaigo"),
]

class ApplicationForm(forms.Form):
    company_id = forms.IntegerField(required=False)
    applicant_name = forms.CharField(max_length=200)
    applicant_email = forms.EmailField()
    phone = forms.CharField(max_length=50, required=False)
    position = forms.CharField(max_length=200, required=False)

    # ✅ add these
    location = forms.CharField(max_length=200)
    visa_type = forms.ChoiceField(choices=VISA_CHOICES)

    # ✅ files (names MUST match apply.html)
    cv = forms.FileField()
    work_history = forms.FileField(required=False)
    video = forms.FileField()
