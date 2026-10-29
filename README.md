# Evidence Vault API

API REST para custodiar ficheros con valor probatorio: cada fichero se registra con su huella SHA-256 y un sello de tiempo, toda acción sobre él queda anotada en una cadena de custodia, y un endpoint pide a un modelo de lenguaje un resumen del documento.

Construida con **Python 3.12, FastAPI, SQLAlchemy 2 y PostgreSQL**, con autenticación JWT, pruebas con pytest, imagen Docker y despliegue con Docker Compose. La integración continua pasa el linter y las pruebas en cada push y comprueba que la imagen construye.

## Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| `POST` | `/auth/register` | Crea una cuenta (correo y contraseña). |
| `POST` | `/auth/login` | Devuelve un token JWT (formulario OAuth2). |
| `GET` | `/auth/me` | Usuario autenticado. |
| `POST` | `/evidence` | Sube un fichero, calcula su SHA-256 y abre su cadena de custodia. |
| `GET` | `/evidence` | Lista las evidencias del usuario. |
| `GET` | `/evidence/{id}` | Una evidencia con todos sus eventos de custodia. |
| `GET` | `/evidence/{id}/custody` | Comprueba que la cadena de custodia no se ha manipulado. |
| `POST` | `/evidence/{id}/verify` | Compara un fichero con la huella registrada: detecta cualquier alteración. |
| `POST` | `/evidence/{id}/summary` | Resume el documento con Claude y lo anota en la custodia. |
| `GET` | `/health` | Estado del servicio. |

La documentación interactiva se genera sola en `/docs`.

## Ejecutar en local

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # ajusta DATABASE_URL o deja SQLite para probar
uvicorn app.main:app --reload
```

Con Docker, base de datos incluida:

```bash
docker compose up --build
```

## Pruebas

```bash
pytest
```

Las pruebas corren contra una base de datos SQLite temporal, sin necesitar PostgreSQL. La llamada al modelo de lenguaje se sustituye por una función fija en las pruebas para no depender de la red.

## Estructura

```
app/
  main.py          punto de entrada, creación de tablas y /health
  config.py        configuración por variables de entorno (.env)
  db.py            motor y sesión de SQLAlchemy
  models.py        tablas: users, evidences, custody_events
  schemas.py       esquemas Pydantic de entrada y salida
  security.py      bcrypt y JWT
  deps.py          dependencia get_current_user
  routers/auth.py  registro, login y perfil
  routers/evidence.py  la bóveda
  services/hashing.py     SHA-256 por bloques
  services/custody.py     huellas encadenadas de la cadena de custodia
  services/summarizer.py  resumen con Claude
tests/             pytest: salud, autenticación y bóveda
```

## Decisiones de diseño

- **La huella se calcula por bloques** para poder custodiar ficheros grandes sin cargarlos en memoria.
- **La cadena de custodia está encadenada con huellas**: cada evento guarda el SHA-256 del anterior y el suyo propio. Si alguien edita cualquier evento, o borra uno que no sea el último, directamente en la base de datos, la cadena se rompe en ese punto y `/evidence/{id}/custody` lo detecta. Borrar el último evento no se detecta solo con esto: haría falta publicar la última huella fuera del sistema (por ejemplo, con un sello de tiempo externo).
- **Cada usuario solo ve lo suyo**: una evidencia ajena responde 404, no 403, para no revelar que existe.
- **Las pruebas no tocan servicios externos**: ni PostgreSQL ni la API de Claude.

## Cómo se ha hecho

Proyecto personal desarrollado con asistencia de IA (Claude Code): el diseño, las decisiones y la revisión del código son míos, y la IA me ha ayudado a escribir y probar las distintas partes.

## Próximos pasos

- Migraciones con Alembic en lugar de `create_all`.
- Certificado de custodia en PDF descargable.
- Despliegue detrás de Nginx con TLS.

---

## English summary

REST API to keep files as evidence: every file is registered with its SHA-256 digest and a timestamp, every action is appended to a hash-chained chain of custody that detects tampering, and an endpoint asks a language model for a summary of the document. Python 3.12, FastAPI, SQLAlchemy 2, PostgreSQL, JWT auth, pytest, Docker Compose and GitHub Actions. Built with AI assistance (Claude Code).
