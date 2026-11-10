# Imagen de IdA. El framework base no tiene dependencias; los extras traen las de cada mundo.
#   docker build -t ida .                       # crafter, ajedrez y observabilidad
#   docker build -t ida --build-arg SNAKE=1 .   # además Playwright + Chromium para Snake
#   docker build -t ida-dev --target dev .      # tests, ruff y mypy (lo usa el devcontainer)

FROM python:3.15-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
WORKDIR /app
ARG EXTRAS="crafter,ajedrez,observabilidad"
ARG SNAKE=0
COPY pyproject.toml README.md LICENSE NOTICE ./
COPY ida ./ida
RUN pip install -e ".[${EXTRAS}]" \
 && if [ "$SNAKE" = "1" ]; then pip install -e ".[snake]" && python -m playwright install --with-deps chromium; fi


FROM base AS dev
ARG EXTRAS="crafter,ajedrez,observabilidad"
RUN pip install -e ".[dev,${EXTRAS}]"
COPY tests ./tests
CMD ["python", "-m", "pytest", "-q"]


FROM base AS ida
# Los datos (linaje, memoria SQLite, bioma de archivos) van a un volumen.
RUN useradd --create-home ida && mkdir -p /app/datos && chown -R ida /app/datos
USER ida
VOLUME ["/app/datos"]
# Panel de telemetría (--ver)
EXPOSE 8000
ENV IDA_TELEMETRIA_HOST=0.0.0.0
ENTRYPOINT ["python", "-m", "ida"]
CMD ["--mundo", "minimo", "--latidos", "300", "--semilla", "3", "--cada", "10"]
