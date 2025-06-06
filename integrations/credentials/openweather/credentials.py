from integrations.credentials.base import BaseCredentialsType
from integrations.credentials.openweather.schema import (
    OpenWeatherCredentialsSchema,
    OpenWeatherCredentialsPrivateSchema
)


class OpenWeatherCredentials(BaseCredentialsType):
    """
    Credentials for OpenWeather API integration.
    """
    id = "open_weather"
    name = "OpenWeather API Key"

    def __init__(self, instance):
        super().__init__(instance)

    @classmethod
    def get_credentials_schema(cls):
        """
        Returns the schema dictionary for provider configuration.
        """
        return OpenWeatherCredentialsSchema

    @classmethod
    def get_credentials_private_schema(cls):
        """
        Returns the private schema dictionary for provider configuration.
        """
        return OpenWeatherCredentialsPrivateSchema

    def validate_credentials(self, credentials):
        """
        Validates the provided credentials.
        """
        private_data = self.get_credentials_type_private_data_obj()
        if not private_data.api_key or len(private_data.api_key) < 10:
            raise ValueError("API Key inválida")

    @property
    def get_name(self) -> str:
        """
        Returns the name of the credentials type for display in the admin.
        """
        return self.name

    @property
    def api_key(self):
        """
        Retorna a API key para autenticação.
        """
        private_data_obj = self.get_credentials_type_private_data_obj()
        if hasattr(private_data_obj, "api_key"):
            return private_data_obj.api_key
        raise AttributeError("O atributo 'api_key' não está definido no objeto retornado.")

    @property
    def base_url(self):
        """
        Retorna a URL base para requisições da API.
        """
        data_obj = self.get_credentials_type_data_obj()
        if hasattr(data_obj, "base_url"):
            return data_obj.base_url
        raise AttributeError("O atributo 'base_url' não está definido no objeto retornado.")
