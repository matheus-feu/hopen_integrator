from django import forms

from .models import CredentialsEntity, Integration
from .registry import plugin_registry


class BaseCredentialsEntityAdminForm(forms.ModelForm):
    """
    Base form for CredentialsEntity admin with common fields and methods.
    """

    class Meta:
        model = CredentialsEntity
        fields = [
            'name',
            'handle',
            'credentials_type_id',
            'credentials_type_data',
            'credentials_type_private_data',
            'is_active',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['handle'].required = False


class CredentialsTypeAdminForm(forms.ModelForm):
    """
    Form for selecting the credentials type for a CredentialsEntity.
    """
    credentials_type_id = forms.ChoiceField(
        label='Tipo de credencial',
        required=True
    )

    class Meta:
        fields = ['credentials_type_id']
        model = CredentialsEntity

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        installed_credentials = CredentialsEntity.objects.values_list('credentials_type_id', flat=True)
        avaliable_choices = [
            choice for choice in plugin_registry.get_credentials_types_choices()
            if choice[0] not in installed_credentials
        ]
        self.fields['credentials_type_id'].choices = avaliable_choices


class BaseIntegrationAdminForm(forms.ModelForm):
    """
    Base form for Integration admin with common fields and methods.
    """
    provider_backend_id = forms.ChoiceField(
        label='Provedor da Integração',
        required=True
    )

    class Meta:
        model = Integration
        fields = [
            'provider_backend_id',
            'is_active',
            'enable_logging',
            'name',
            'handle',
            'credentials',
            'provider_backend_data',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['handle'].required = False
        self.fields['provider_backend_id'].choices = plugin_registry.get_provider_backends_choices()

    def clean_handle(self):
        handle = self.cleaned_data.get('handle')
        if not handle:
            return handle

        qs = Integration.objects.filter(handle=handle)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError('Esse identificador já está em uso.')

        return handle

    def clean_provider_backend_data(self):
        provider_backend_id = self.cleaned_data.get('provider_backend_id')
        provider_backend = plugin_registry.get_provider_backend(provider_backend_id)

        if not provider_backend:
            raise forms.ValidationError('Provedor de integração inválido')

        try:
            data = provider_backend.validate_data(self.cleaned_data['provider_backend_data'])
        except Exception as e:
            msg = " | ".join(err["msg"] for err in e.errors()) if hasattr(e, "errors") else str(e)
            raise forms.ValidationError(msg)

        return data


class IntegrationProviderBackendAdminForm(forms.ModelForm):
    provider_backend_id = forms.ChoiceField(
        label='Provedor da Integração',
        required=True
    )

    class Meta:
        fields = ['provider_backend_id']
        model = Integration

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        used_providers = Integration.objects.values_list('provider_backend_id', flat=True)
        available_choices = [
            choice for choice in plugin_registry.get_provider_backends_choices()
            if choice[0] not in used_providers
        ]
        self.fields['provider_backend_id'].choices = available_choices
