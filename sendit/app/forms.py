from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from app.models import Booking, InventoryItem, Message, MoveTask, MovingCompany, Profile


def _style_form_fields(form):
    """Apply Bootstrap classes to every field on a form without repeating
    widget declarations for each one."""
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs.setdefault("class", "form-check-input")
        elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
            widget.attrs.setdefault("class", "form-select")
        elif isinstance(widget, forms.CheckboxSelectMultiple):
            pass  # rendered item-by-item in templates
        else:
            widget.attrs.setdefault("class", "form-control")


class RegisterForm(UserCreationForm):
    """Registration using Django's built-in, secure password hashing
    (the original project stored raw passwords in a plain CharField —
    that is never done here)."""

    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    role = forms.ChoiceField(choices=Profile.Role.choices, initial=Profile.Role.CLIENT)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "phone_number", "role", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_form_fields(self)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                role=self.cleaned_data["role"],
                phone_number=self.cleaned_data.get("phone_number", ""),
            )
        return user


class StyledAuthenticationForm(AuthenticationForm):
    """Same behaviour as Django's built-in login form, just with Bootstrap
    classes applied so it matches the rest of the design system."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_form_fields(self)


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()

    class Meta:
        model = Profile
        fields = ["phone_number", "bio", "address"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        _style_form_fields(self)
        if self.user:
            self.fields["first_name"].initial = self.user.first_name
            self.fields["last_name"].initial = self.user.last_name
            self.fields["email"].initial = self.user.email

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if self.user:
            self.user.first_name = self.cleaned_data["first_name"]
            self.user.last_name = self.cleaned_data["last_name"]
            self.user.email = self.cleaned_data["email"]
            if commit:
                self.user.save()
        return profile


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            "date", "moving_time", "current_address", "destination_address",
            "property_type", "bedrooms", "services",
            "crew_size", "vehicle_size", "emergency_contact_name",
            "emergency_contact_phone_number", "relationship_to_user",
            "instructions", "accept_terms", "special_items",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "moving_time": forms.TimeInput(attrs={"type": "time"}),
            "instructions": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_form_fields(self)


class QuoteSelectionForm(forms.Form):
    """Lets a client pick 1–2 moving companies to compare quotes for."""

    companies = forms.ModelMultipleChoiceField(
        queryset=MovingCompany.objects.all(),
        widget=forms.CheckboxSelectMultiple,
    )

    def clean_companies(self):
        companies = self.cleaned_data["companies"]
        if not (1 <= len(companies) <= 2):
            raise forms.ValidationError("Please select one or two moving companies.")
        return companies


class MoveTaskForm(forms.ModelForm):
    class Meta:
        model = MoveTask
        fields = ["title", "due_date"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_form_fields(self)


class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ["name", "category", "quantity", "is_fragile", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_form_fields(self)


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["content"]
        widgets = {"content": forms.Textarea(attrs={"rows": 2, "placeholder": "Write a message..."})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_form_fields(self)


class MovingCompanyForm(forms.ModelForm):
    """Used by admins to add/edit moving companies."""

    class Meta:
        model = MovingCompany
        fields = [
            "name", "description", "logo", "base_price", "price_per_bedroom",
            "price_per_crew_member", "rating", "years_in_business",
            "is_verified", "phone_number", "email",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_form_fields(self)
