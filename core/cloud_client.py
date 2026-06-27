import os
from dataclasses import dataclass
from openai import OpenAI

@dataclass
class CloudResponse:
    content: str
    model: str
    provider: str

class CloudClient:
    def __init__(self, provider='groq'):
        self.provider = provider
        self.api_key = os.environ.get('GROQ_API_KEY')
        self.model = os.environ.get('CLOUD_MODEL', 'llama-3.3-70b-versatile')
        self.client = OpenAI(
            api_key=self.api_key,
            base_url='https://api.groq.com/openai/v1'
        )

    def complete(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1024
        )
        return CloudResponse(
            content=response.choices[0].message.content,
            model=self.model,
            provider=self.provider
        )
