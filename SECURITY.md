# Seguridad

IdA es un proyecto experimental para ejecutar en local. No está pensado para exponerse a una red ni para manejar datos de terceros.

## Componentes con riesgo y medidas por defecto

| Componente | Riesgo | Medida por defecto |
|---|---|---|
| Mundo de archivos (`ida/mundos/archivos.py`) | Sus acciones crean, mueven y borran ficheros, y al empezar borra y regenera su bioma | Todo se confina al bioma (`datos/archivos/bioma` por defecto): cada ruta se normaliza (`..`, rutas absolutas) y se rechaza si sale de él. Lo comprueba `tests/test_mundo_archivos.py`. **No resuelve enlaces simbólicos**: no crees enlaces dentro del bioma que apunten fuera |
| Panel de telemetría (`--ver`) | Servidor HTTP sin autenticación | Escucha solo en `127.0.0.1`. En un contenedor escucha en `0.0.0.0` (variable `IDA_TELEMETRIA_HOST`), y `docker-compose.yml` publica el puerto solo en `127.0.0.1` del anfitrión |
| Pila de observabilidad (`docker compose`) | Collector, Jaeger, Prometheus y Grafana sin autenticación | Todos los puertos se publican solo en `127.0.0.1`. Grafana entra en modo anónimo de solo lectura. No uses esta configuración en un servidor expuesto |
| Snake (Playwright) | Automatiza un sitio de terceros (https://playsnake.org/) | No usa credenciales. Si el sitio cambia o deja de funcionar, el mundo deja de funcionar. Respeta sus condiciones de uso |
| Stockfish | Ejecutable externo | No se distribuye. Solo se lanza si se indica `--opcion stockfish=RUTA` |

## Secretos

- Ningún componente necesita claves de API ni credenciales.
- `.env` está en `.gitignore`.

## Cómo avisar de un problema

Abre un *issue* en GitHub con el prefijo `[seguridad]` sin incluir detalles explotables, y se acordará un canal privado.
