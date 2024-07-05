from operator import itemgetter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from conversation import CustomChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

from azure_config import azure_llm, azure_embeddings
from constants import RAG_PROMPT
from rag_fusion import rag_fusion_chain

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = CustomChatMessageHistory()
    return store[session_id]

store = {}
llm = azure_llm()
embeddings = azure_embeddings()

# RAG
system_prompt = RAG_PROMPT
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

context_chain = rag_fusion_chain()
full_chain = context_chain | prompt | llm | StrOutputParser()

full_chain_with_context = context_chain | {"answer": prompt | llm | StrOutputParser(), "context": itemgetter("context")}

full_chain_with_message_history = RunnableWithMessageHistory(
    full_chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)

full_chain_with_context_and_message_history = RunnableWithMessageHistory(
    full_chain_with_context,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)

# Function to invoke the full chain
def caller(message, sess_id):
    print(sess_id)
    print("Store:", store)
    response = full_chain_with_message_history.invoke(
        {"question": message},
        config={"configurable": {"session_id": sess_id}})
    return response

def caller_with_context(message, sess_id):
    # print(sess_id)
    # print("Store:", store)
    response = full_chain_with_context_and_message_history.invoke(
        {"question": message},
        config={"configurable": {"session_id": sess_id}})
    return response