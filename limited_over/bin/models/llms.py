class BaseCricketLLMOptions():

    def __init__(self):
        self.model = "google/gemma-4-e4b"
        self.endpoint = "http://10.0.2.2:1234/v1" # defaults to None for OpenAI
        self.api_key = "sk" # Cannot be empty or None
        self.system_identifier = "human" if self.model == "mistral" else "system"
