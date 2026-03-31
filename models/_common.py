from dify_plugin.errors.model import (
    InvokeAuthorizationError,
    InvokeBadRequestError,
    InvokeConnectionError,
    InvokeError,
    InvokeRateLimitError,
    InvokeServerUnavailableError,
)


class _CommonZhipuaiCoding:
    def _to_credential_kwargs(self, credentials: dict) -> dict:
        credentials_kwargs = {
            "api_key": credentials.get("api_key", ""),
        }

        if credentials.get("base_url"):
            credentials_kwargs["base_url"] = credentials["base_url"]
        else:
            credentials_kwargs["base_url"] = "https://open.bigmodel.cn/api/coding/paas/v4/"

        return credentials_kwargs

    @property
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        return {
            InvokeConnectionError: [],
            InvokeServerUnavailableError: [],
            InvokeRateLimitError: [],
            InvokeAuthorizationError: [],
            InvokeBadRequestError: [],
        }
