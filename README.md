# Pipeline de extracción técnica

Este proyecto es mi segunda pre-entrega del curso de AI Engineering. Le paso un texto sobre un incidente técnico y el programa devuelve en JSON las tecnologías que se mencionan, el nivel de criticidad y un resumen corto. Lo hice con Python 3.14, LangChain, Pydantic y OpenAI.

## Cómo ejecutarlo

Desde la carpeta del proyecto, en PowerShell, creá un entorno virtual e instalá las dependencias. Si ya tenés `.venv`, podés saltar el primer comando.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copiá [`.env.example`](.env.example) a `config/.env` si todavía no lo creaste.

```powershell
New-Item -ItemType Directory -Force config | Out-Null
if (-not (Test-Path -LiteralPath .\config\.env)) {
    Copy-Item .\.env.example .\config\.env
}
```

Completá `OPENAI_API_KEY` con tu clave y dejá `OPENAI_MODEL=gpt-4o-mini` o indicá otro modelo al que tengas acceso. El archivo `config/.env` queda fuera de Git.

## Los dos ejemplos

Los dos comandos hacen una consulta a OpenAI. El texto del resumen y la criticidad de los ejemplos de salida pueden variar.

### 1. Caída del servicio de autenticación

```powershell
.\.venv\Scripts\python.exe main.py
```

El texto dice que se cayó el servicio de autenticación y que algunas personas no pudieron iniciar sesión. Se conoce el síntoma y el efecto, aunque todavía no se sabe qué componente falló ni si el problema sigue activo. Como no se nombra ninguna tecnología concreta, se espera una lista vacía. Una criticidad posible es `alta` por la caída del servicio.

```json
{
  "tecnologias": [],
  "nivel_de_criticidad": "alta",
  "resumen_tecnico": "La caída del servicio de autenticación impidió iniciar sesión a algunas personas, y se desconoce qué componente falló o si el problema sigue activo."
}
```

### 2. Caso ambiguo

```powershell
.\.venv\Scripts\python.exe main.py --ambiguo
```

El texto solo dice que algo dejó de responder por un rato. Acá interesa ver si el modelo conserva la incertidumbre. `tecnologias` debería ser `[]` y el resumen debería dejar claro que se desconoce el componente afectado y si el incidente se resolvió. Pydantic comprueba que la criticidad sea `baja`, `media` o `alta`. El valor concreto depende de cómo el modelo interprete el texto.

```json
{
  "tecnologias": [],
  "nivel_de_criticidad": "media",
  "resumen_tecnico": "Se reportó una falla temporal en un componente sin identificar y se desconoce si el problema se resolvió."
}
```

## Cómo está armado

- `schemas.py` define los tres campos obligatorios y los valores de criticidad. Dentro de Python los nombres están en inglés. Los alias de Pydantic conservan los nombres en castellano en el JSON.
- `chain.py` arma el prompt y lo conecta con el modelo y la validación usando LCEL. `process_text()` ejecuta la cadena con `.ainvoke()` y devuelve una extracción validada.
- `main.py` elige el texto de ejemplo, llama al pipeline e imprime el JSON.

Si la respuesta llega truncada o falla la validación, se vuelve a consultar al modelo hasta un máximo de tres intentos con el mismo timeout. Ante un timeout de red, la siguiente consulta pasa de 30 a 45 segundos y, si vuelve a vencer, a 60. Esos tiempos corresponden a la espera de red. La ejecución completa puede tardar más por los reintentos.

Probé el recorrido y los reintentos con respuestas simuladas. Los logs de la demo muestran qué pasó con la validación y si hubo un reintento.
