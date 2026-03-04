from os import environ

import httpx
from retry import retry

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger

OPENAI_RETRIES = 5


class OpenAIHandler(BaseAiHandler):
    def __init__(self):
        try:
            super().__init__()
            self.api_key = get_settings().ic_code.key
            self.base_url = get_settings().ic_code.base_url
        except AttributeError as e:
            raise ValueError("IC Code key is required") from e

    @property
    def deployment_id(self):
        """
        Returns the deployment ID for the OpenAI API.
        """
        return get_settings().get("OPENAI.DEPLOYMENT_ID", None)

    @retry(exceptions=(httpx.HTTPStatusError, httpx.TimeoutException, AttributeError),
           tries=OPENAI_RETRIES, delay=2, backoff=2, jitter=(1, 3))
    async def chat_completion(self, model: str, system: str, user: str,
                              temperature: float = 0.2):
        try:
            get_logger().info(f"System: {system[:100]}...")
            get_logger().info(f"User: {user[:100]}...")

            messages = [{"role": "user", "content": system + "\n" + user}]

            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "ic_coding_assistant",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 8000,
            }

            async with httpx.AsyncClient(timeout=90) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

            resp = data["choices"][0]["message"]["content"]
            finish_reason = data["choices"][0].get("finish_reason", "stop")
            usage = data.get("usage", {})

            get_logger().info(f"AI response", response=resp, finish_reason=finish_reason,
                              model=model, usage=usage)
            return resp, finish_reason

        except httpx.HTTPStatusError as e:
            get_logger().error(f"HTTP error during AI inference: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.TimeoutException as e:
            get_logger().error(f"Timeout during AI inference: {e}")
            raise
        except Exception as e:
            get_logger().error(f"Unknown error during AI inference: {e}")
            raise
