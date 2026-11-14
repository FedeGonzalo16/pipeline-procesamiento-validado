import argparse
import asyncio
import logging
from openai import APITimeoutError, OpenAIError
from chain import InvalidConfigurationError, InvalidOutputError, process_text

DEMO_TEXT = (
    "Se cayó el servicio de autenticación y algunas personas no pudieron iniciar sesión."
    "la verdad es que no sabemos qué componente falló ni si el problema sigue activo."
)

AMBIGUOUS_TEXT = (
    "Hay algo que dejó de responder por un rato."
    "No sabemos qué componente falló ni si "
    "el problema no lo resolvimos todavía."
)

async def main(text: str = DEMO_TEXT) -> None:
    result = await process_text(text)
    print(result.model_dump_json(indent=2))

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    # Ejemplo de uso: python main.py --ambiguo o python main.py para el caso de demo
    parser = argparse.ArgumentParser(description="Demostración del pipeline de extracción técnica.")
    parser.add_argument(
        "--ambiguo",
        dest="ambiguous",
        action="store_true",
        help="Analiza un caso sin tecnologías identificadas y con impacto incierto.",
    )
    args = parser.parse_args()
    text = AMBIGUOUS_TEXT if args.ambiguous else DEMO_TEXT

    """ Pipelline de extracción técnica"""
    try:
        asyncio.run(main(text))
    except (InvalidConfigurationError, InvalidOutputError) as exc:
        logging.error("%s", exc)
        raise SystemExit(1) from None
    except APITimeoutError:
        logging.error("Se agotaron los intentos por tiempo de espera de red.")
        raise SystemExit(1) from None
    except OpenAIError as exc:
        logging.error("Falló la consulta a OpenAI (%s).", type(exc).__name__)
        raise SystemExit(1) from None
