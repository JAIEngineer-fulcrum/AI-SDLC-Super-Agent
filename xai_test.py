from langchain_xai import ChatXAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from dotenv import load_dotenv

load_dotenv()

chat = ChatXAI(  
    model="grok-4-fast-reasoning"
)

lm = HuggingFaceEndpoint(
    repo_id="deepseek-ai/DeepSeek-V3.2-Exp",
    task='text-generation'
)

model = ChatHuggingFace(llm=lm)

# ans2 = model.invoke("What is the name of the technology used to build AI powered applications")
messages = [
    (
        "system",
        "You are a helpful assistant that translates English to French. Translate the user sentence.",
    ),
    ("human", "I love programming."),
]
ai_msg = chat.invoke(messages)
print(ai_msg.content)