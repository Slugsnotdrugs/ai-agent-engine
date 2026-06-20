import os, urllib.request, json
from dataclasses import dataclass

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
        self.url = 'https://api.groq.com/openai/v1/chat/completions'

    def complete(self, messages):
        data = json.dumps({'model': self.model, 'messages': messages, 'max_tokens': 1024}).encode()
        req = urllib.request.Request(self.url, data=data, headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as r:
            result = json.loads(r.read())
        return CloudResponse(content=result['choices'][0]['message']['content'], model=self.model, provider=self.provider)
