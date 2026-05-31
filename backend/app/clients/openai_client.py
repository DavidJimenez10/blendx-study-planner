import instructor
from openai import APIConnectionError, APITimeoutError, OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class OpenAIClient:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = instructor.from_openai(OpenAI(api_key=api_key))
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
