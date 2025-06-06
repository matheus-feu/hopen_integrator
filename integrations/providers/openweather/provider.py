from datetime import datetime

import requests

from integrations.credentials.openweather.credentials import OpenWeatherCredentials
from integrations.providers.base import BaseProviderBackend
from integrations.providers.openweather.config import OpenWeatherConfig, NormalizedDataSchema


class OpenWeatherProviderBackend(BaseProviderBackend):
    id = "open_weather"
    name = "OpenWeather API"
    category = "weather"
    allowed_credentials_types = ["open_weather"]

    def __init__(self, integration=None, credentials=None):
        """
        Initializes the OpenWeather provider with the given credentials.
        :param integration: The integration instance.
        :param credentials: An instance of OpenWeatherCredentials or a dictionary with credentials data.
        """
        if credentials and not isinstance(credentials, OpenWeatherCredentials):
            credentials = OpenWeatherCredentials(credentials)
        super().__init__(integration=integration, credentials=credentials)
        self.request_data = {}

    @classmethod
    def get_category(cls):
        return cls.category

    @classmethod
    def get_schema_dict(cls, integration=None):
        """
        Returns the Pydantic schema dictionary for provider backend data.
        This is used to build the configuration form in the admin interface.
        """
        return cls.get_provider_backend_data_config().model_json_schema()

    @classmethod
    def get_provider_backend_data_config(cls):
        """
        Returns the Pydantic schema class for provider backend data.
        This schema defines the configuration for the OpenWeather provider.
        """
        return OpenWeatherConfig

    @classmethod
    def validate_data(cls, data):
        """
        Valida os dados adicionais usando o modelo Pydantic.
        """
        validated = OpenWeatherConfig(**data)
        return validated.model_dump()

    def normalize(self, raw_data: dict) -> dict:
        timestamp = datetime.utcfromtimestamp(int(raw_data.get("dt"))) if raw_data.get("dt") else None
        return NormalizedDataSchema(
            temperature=raw_data.get("main", {}).get("temp"),
            humidity=raw_data.get("main", {}).get("humidity"),
            weather=raw_data.get("weather", [{}])[0].get("description"),
            city=raw_data.get("name"),
            country=raw_data.get("sys", {}).get("country"),
            timestamp=timestamp,
        ).model_dump()

    def fetch(self):
        """
        Busca e normaliza os dados da API.
        :return: Lista com o dicionário dos dados normalizados ou erro.
        """
        base_url = str(self.credentials.base_url).rstrip("/") + "/weather"
        api_key = self.credentials.api_key

        self.request_data = {
            "appid": api_key,
            "q": self.config.city,
            "lang": self.config.language,
        }
        try:
            response = requests.get(base_url, params=self.request_data)
            response.raise_for_status()
            raw_data = response.json()
            normalized_data = self.normalize(raw_data)

            self.save_log(
                success=True,
                message="Dados do clima obtidos com sucesso.",
                method="fetch",
                records_imported=1,
                request_data=self.request_data,
                response_data=normalized_data,
            )
            return [normalized_data]

        except Exception as e:
            self.save_log(
                success=False,
                message=f"Erro ao buscar dados: {e}",
                method="fetch",
                records_imported=0,
                request_data=self.request_data,
                response_data={},
            )
            return []
