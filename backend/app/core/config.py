"""Application settings.

Values are read from environment variables, falling back to `backend/.env`.
Sections must never read `os.environ` directly — import ``settings`` from here.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_name: str = "CreditMate API"
    app_version: str = "0.1.0"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    # Comma-separated in the environment, e.g. "http://localhost:3000,http://127.0.0.1:3000"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # --- Supabase ---
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # --- AI Credit Assistant section ---
    openai_api_key: str = ""

    # --- Card Storage section (Plaid) ---
    # Sandbox keys come from https://dashboard.plaid.com/team/keys.
    plaid_client_id: str = ""
    plaid_secret: str = ""
    # "sandbox" or "production"; the section only talks to sandbox for now.
    plaid_env: str = "sandbox"
    # Sandbox institution used when no access token is supplied. `ins_56` (Chase)
    # ships a credit card account with liabilities + transactions in Sandbox.
    plaid_sandbox_institution_id: str = "ins_56"
    # Optional: reuse an existing sandbox Item instead of creating one per sync.
    plaid_access_token: str = ""

    # --- Cost to Buy section (Gemini vision for price extraction) ---
    # Key from https://aistudio.google.com/apikey. Used to read a product name and
    # price out of a photo of a price tag or a product screenshot.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"

    @property
    def cors_origin_list(self) -> list[str]:
        """Allowed browser origins, parsed from the comma-separated setting."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env.strip().lower() in {"dev", "development", "local"}

    @property
    def plaid_base_url(self) -> str:
        """Plaid API host for the configured environment."""
        if self.plaid_env.strip().lower() == "production":
            return "https://production.plaid.com"
        return "https://sandbox.plaid.com"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()


settings = get_settings()
