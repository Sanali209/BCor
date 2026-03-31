
# Import Libraries
import os
from typing import Any, List, Mapping, Optional
from langchain.llms.base import LLM
import google.generativeai as genai


#login(token="")
# --- API Key (замените на свой, если необходимо) ---
GOOGLE_AI_STUDIO_API_KEY = "AIzaSyB2n4fQmeKYpGId5qdWdClp1wHEnz0vQic"
genai.configure(api_key=GOOGLE_AI_STUDIO_API_KEY)

# --- Кастомная LLM для Gemini ---
class GeminiLLM(LLM):
    model_name: str = "gemini-1.5-flash"

    @property
    def _llm_type(self) -> str:
        return "gemini"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        model = genai.GenerativeModel(self.model_name)
        response = model.generate_content(prompt)
        return response.text

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"model_name": self.model_name}

def LLM_hugingface_model_inference(model_name="google/gemma-7b", temperature=0.1, max_length=4096):
    """
    Google
    Flant models: https://huggingface.co/collections/google/flan-t5-release-65005c39e3201fff885e22fb
    Gemma models: https://huggingface.co/collections/google/gemma-release-65d5efbccdbb8c4202ec078b
    Mistral models: https://huggingface.co/mistralai
    @param model_name:
    @return:
    """
    return HuggingFaceHub(repo_id=model_name,
                          model_kwargs={"temperature": temperature,
                                        "max_length": max_length})

def vhat_bot_llm(model_name="google/gemma-7b", temperature=0.1, max_length=4096):
    chat_bot_pipline = pipeline("text-generation", model=model_name, framework="pt")
    prompt = PromptTemplate(input_variables=["user_input"],
    template="The user said: {user_input}. Respond appropriately.")