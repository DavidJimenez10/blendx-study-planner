import instructor
from openai import APIConnectionError, APITimeoutError, OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class OpenAIClient:
    def __init__(self, api_key: str, model: str) -> None:
        self.raw_client = OpenAI(api_key=api_key)
        self.client = instructor.from_openai(self.raw_client)
        self.model = model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((APIConnectionError, APITimeoutError)),
    )
    def generate_tasks(self, prompt: str, response_model: type) -> list:
        return self.client.chat.completions.create(
            model=self.model,
            response_model=response_model,
            messages=[{"role": "user", "content": prompt}],
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((APIConnectionError, APITimeoutError)),
    )
    def generate_embedding(self, text: str) -> list[float]:
        response = self.raw_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((APIConnectionError, APITimeoutError)),
    )
    def chat(self, messages: list[dict[str, str]]) -> str:
        response = self.raw_client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content or ""
