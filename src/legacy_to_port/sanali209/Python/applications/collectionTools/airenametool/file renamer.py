import os

from langchain.chains import LLMChain

from SLM.LangChain.LangChainHelper import LLM_hugingface_model_inference

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

os.environ['HUGGINGFACEHUB_API_TOKEN'] = os.getenv('HUGGING_FACE_TOKEN', '')
from langchain_core.prompts import PromptTemplate

file_name = "avengers_107.jpg"

template_string = (
    """
    INSTRUCTIONS:
    you are given a one filename. You need to determine if the filename is human readable or not.
    end the answer with 
    ---------------------------------------
    EXAMPLES:
    filename: 37019507112_f2d61af76a_b.jpg
    answer: no
    
    filename: Awesome_3D_Fan_Art_Inspiration_006.jpg
    answer: yes
    
    filename: avatar-world-of-warcraft-youtube-deviantart-png-favpng-vGtmAxTRukvPZRsB3zSdQ1ttZ.jpg
    answer:partially
    ------------------------------------------------------------
    ANSWER FORMAT:
    JSON
    {{"readable": "no","reason": "is random string of numbers and letters with no spaces or special characters. It is not human readable."}}
    ------------------------------------------------------------
    Question:
    filename: {file_name}
    answer:{{"""
)

prompt = PromptTemplate.from_template(template_string)

model = LLM_hugingface_model_inference(model_name='mistralai/Mistral-7B-Instruct-v0.2')

llm_chain = LLMChain(prompt=prompt, llm=model)

print(llm_chain.run(file_name))
