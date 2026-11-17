import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from openai import APITimeoutError
from schemas import TechnicalExtraction

logger = logging.getLogger(__name__)

FORMAT_INSTRUCTIONS = """
- nivel_de_criticidad: usá alta si hay una caída o un impacto grave,
  media si hay degradación parcial y baja si es informativo o de bajo impacto.
- Si el texto deja dudas, reflejalas en el resumen.
"""

# Excepciones controladas
class InvalidConfigurationError(ValueError):
    """Falta una variable necesaria para la config de OpenAI."""

class InvalidOutputError(ValueError):
    """La salida del modelo no cumple el esquema esperado."""

# Las reglas en sistema y el texto a analizar en humano.
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Extraé información técnica a partir del texto recibido.\n\n"
            "{format_instructions}",
        ),
        ("human", "{text}"),
    ]
).partial(format_instructions=FORMAT_INSTRUCTIONS)  

def create_model(timeout: float = 30.0) -> ChatOpenAI:
    env_path = Path(__file__).resolve().parent / "config" / ".env"
    load_dotenv(env_path)

    model_name = os.getenv("OPENAI_MODEL", "").strip()
    if not model_name:
        raise InvalidConfigurationError("Falta configurar OPENAI_MODEL.")

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise InvalidConfigurationError("Falta configurar OPENAI_API_KEY.")

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        temperature=0,
        timeout=timeout,
        max_retries=0,
    )

#Vlidamos la salida del modelo y devolvemos un objeto Pydantic.
def validate_output(result: dict) -> TechnicalExtraction:

    raw = result["raw"]
    if raw.response_metadata.get("finish_reason") == "length":
        logger.warning("El modelo cortó la respuesta por límite de tokens.")
        raise InvalidOutputError("Respuesta truncada.")
    parsed = result["parsed"]
    error = result["parsing_error"]
    if error is not None or not isinstance(parsed, TechnicalExtraction):
        logger.warning("La salida del modelo no cumple el esquema esperado.")
        raise InvalidOutputError("Respuesta inválida o incompleta.") from error

    logger.info("Extracción técnica exitosa.")
    return parsed

"""Analisis de entrada asíncronamente  y devolvemos una extracción Pydantic."""
async def process_text(text: str) -> TechnicalExtraction:
    if not text.strip():
        raise ValueError("El texto de entrada está vacío.")
    # Timeouts de red incrementales
    timeouts = (30.0, 45.0, 60.0)
    # recorremos cada intento, con su timeout asignado, hasta que no queden +, = excepción de timeout.
    for attempt, timeout in enumerate(timeouts, start=1):
        model = create_model(timeout=timeout)
        # Configuramos el modelo con salida estructurada.
        structured_model = model.with_structured_output(
            TechnicalExtraction,
            method="function_calling",
            include_raw=True,
        )
        extraction = (structured_model | RunnableLambda(validate_output)).with_retry(
            retry_if_exception_type=(InvalidOutputError,),
            stop_after_attempt=3,
            wait_exponential_jitter=False,
        )
        # En LCEL, con | pasamos la salida del prompt al siguiente paso.
        chain = prompt | extraction

        try:
            return await chain.ainvoke({"text": text})
        except APITimeoutError:
            if attempt == len(timeouts):
                raise
            logger.warning(
                "Se agotó la espera de red en el intento %s. Reintento con %.0f segundos.",
                attempt,
                timeouts[attempt],
            )
