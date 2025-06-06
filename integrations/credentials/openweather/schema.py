from pydantic import BaseModel, field_validator, HttpUrl, constr


class OpenWeatherCredentialsSchema(BaseModel):
    base_url: HttpUrl = ""


class OpenWeatherCredentialsPrivateSchema(BaseModel):
    api_key: constr(min_length=1, max_length=64)

    @field_validator('api_key', mode='after')
    def api_key_must_be_valid(cls, value):
        if not value:
            raise ValueError("API Key inválida para OpenWeather.")
        return value
