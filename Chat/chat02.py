import re
import os
from constant import CYPHER_GENERATION_TEMPLATE, CYPHER_QA_TEMPLATE
from loguru import logger
from langchain_community.llms import Ollama
from langchain_community.graphs import Neo4jGraph
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import gradio as gr
from decouple import config as DefaultConfig
from decouple import Config, RepositoryEnv
from langchain_cohere.llms import Cohere

DEV_ENV_FILE = "../.env.dev"
PROD_ENV_FILE = "../.env.prod"

# default env file
DOTENV_FILE = os.environ.get("DOTENV_FILE", DEV_ENV_FILE)

config: Config = DefaultConfig

ENVIORNMENT = os.environ.get('PYTHON_ENV', "dev")

if ENVIORNMENT == "dev":
    config = Config(RepositoryEnv(DEV_ENV_FILE))

'''
Configurations
'''

model = "llama3"

NEO4J_RESOURCE_URI = config('NEO4J_RESOURCE_URI', cast=str)
NEO4J_USERNAME = config('NEO4J_USERNAME', cast=str)
NEO4J_PASSWORD = config('NEO4J_PASSWORD', cast=str)
OLLAMA_BASE_URL = config('OLLAMA_BASE_URL', cast=str)


graph = Neo4jGraph(enhanced_schema=True, url=NEO4J_RESOURCE_URI,
                   username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
graph.refresh_schema()
schema = graph.schema

# llm = Ollama(model=model, base_url=OLLAMA_BASE_URL)
llm = Cohere(cohere_api_key=config('COHERE_API_KEY', cast=str))


CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
)

chain = CYPHER_GENERATION_PROMPT | llm | StrOutputParser()


def extract_cypher(text: str) -> str:
    """Extract Cypher code from a text.

    Args:
        text: Text to extract Cypher code from.

    Returns:
        Cypher code extracted from the text.
    """
    # The pattern to find Cypher code enclosed in triple backticks
    pattern = r"```(.*?)```"

    # Find all matches in the input text
    matches = re.findall(pattern, text, re.DOTALL)

    return matches[0] if matches else text


def get_answer(question):
    logger.info("Question: {}", question)
    args = {
        "question": question,
        "schema": schema,
    }

    answer = chain.invoke(args)
    generated_cypher = extract_cypher(answer)
    logger.debug("Generated cypher:")
    logger.debug(generated_cypher)
    try:
        context = graph.query(generated_cypher)[: 5]
        logger.debug(f"Context: {context}")

        CYPHER_QA_PROMPT = PromptTemplate(
            input_variables=["context", "question"], template=CYPHER_QA_TEMPLATE
        )

        qa_chain = CYPHER_QA_PROMPT | llm | StrOutputParser()

        args = {"question": question, "context": context}
        result = qa_chain.invoke(args)
        logger.info(f"Result: {result}", )
        return result
    except Exception as e:
        logger.error(f"Error: {e}")
        return "I don't know the answer"


with gr.Blocks() as graphChat:
    inputQuery = gr.Text(
        label='query', placeholder='Write query here')
    submit_button = gr.Button('submit', size="lg")

    output_summary = gr.Textbox(
        label="Output", show_copy_button=True)

    submit_button.click(fn=get_answer, inputs=[
                        inputQuery], outputs=[output_summary])

graphChat.launch()


# result = get_answer("who is the founder of BrowserStack company ?")

# print(get_answer("How many Founders are in the graph?"))

# print(get_answer("How many Industries are in the graph?"))

# print(get_answer("How many Companies are in the graph?"))

# print(get_answer("provide crunchbase_url of company in Industry Artificial Intelligence"))

# print(get_answer("Who and When founded company Deel? also what does comapny do ?"))

# print(get_answer("List of founder having company in same industry as Founder Nakul Aggarwal"))

# print(get_answer("List of Companies in Artificial Intelligence industry Big funding"))

# print(get_answer("List of Companies in Artificial Intelligence industry very less funding"))

# print(get_answer("Depending on the funding in, which other industry artificial intelligence is growing ?"))
