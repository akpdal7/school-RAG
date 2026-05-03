from collections.abc import Generator

from llama_index.core.llms import CompletionResponse, CustomLLM, LLMMetadata
from openai import OpenAI
from pydantic import Field, PrivateAttr


class MeshAPILLM(CustomLLM):
    api_key: str = Field(exclude=True)
    api_base: str
    model: str
    metadata_model: str
    temperature: float = 0.1
    max_tokens: int = 1024
    context_window: int = 128000

    _client: OpenAI = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._client = OpenAI(api_key=self.api_key, base_url=self.api_base)

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.max_tokens,
            is_chat_model=True,
            is_function_calling_model=False,
            model_name=self.metadata_model,
        )

    def complete(self, prompt: str, formatted: bool = False, **kwargs) -> CompletionResponse:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
        )
        text = response.choices[0].message.content or ""
        return CompletionResponse(text=text, raw=response)

    def stream_complete(
        self, prompt: str, formatted: bool = False, **kwargs
    ) -> Generator[CompletionResponse, None, None]:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            stream=True,
        )
        for chunk in response:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield CompletionResponse(text=delta, delta=delta, raw=chunk)

