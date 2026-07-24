# Kumateq Catalog Service

Servicio independiente para consultar un catálogo almacenado en Google Sheets.
Valida filas con Pydantic, conserva solo productos activos, detecta duplicados,
mantiene caché y expone una API REST lista para integrarse con WhatsApp o un agente.

## Columnas esperadas

Obligatorias:

`sku`, `nombre`, `categoria`, `descripcion`, `precio`, `moneda`, `stock`, `estado`

Opcionales:

`marca`, `variantes`, `palabras_clave`, `url_producto`, `actualizado_en`

La primera fila debe contener los encabezados. `estado` acepta `activo` o `inactivo`.

## Configuración de Google

1. Crea o selecciona un proyecto en Google Cloud.
2. Habilita Google Sheets API.
3. Crea una cuenta de servicio.
4. Descarga el JSON y guárdalo localmente como
   `credentials/service-account.json`.
5. Comparte la hoja con el correo de la cuenta de servicio como lector.
6. Copia `.env.example` a `.env` y coloca el ID del spreadsheet.

No subas el JSON de credenciales al repositorio.

## Ejecución

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Documentación interactiva: `http://localhost:8000/docs`

## Endpoints

- `GET /health`
- `POST /catalog/refresh`
- `GET /products/{sku}`
- `GET /products?q=camisa+azul&category=Camisas&limit=5`

## Pruebas

```bash
pytest
```

Las pruebas no llaman a Google: reemplazan la fuente por un repositorio falso.

## Decisiones del MVP

- Google Sheets es solo lectura.
- Las filas inválidas se ignoran y aparecen en el reporte de carga.
- Los SKU duplicados se ignoran después de la primera aparición.
- Los productos inactivos no se exponen.
- Los productos con stock cero sí se exponen.
- La caché evita consultar Google por cada mensaje.
- La búsqueda es determinista; todavía no usa IA ni embeddings.


## Simulador de conversaciones en terminal

```cmd
python -m scripts.chat_catalog
```

Prueba consultas como `¿Cuánto cuesta la camisa azul?`, `¿Hay stock del polo negro?`
o `Necesito una cotización por 80 unidades`. Escribe `salir` para terminar.

## Status al 24/07
Hoy hemos testeado en la consola el bot, y cumple con las siguientes tareas:

carga el catálogo desde Google Sheets al iniciar;
busca productos usando el servicio existente;
responde precio, stock y descripción;
informa productos sin stock;
excluye productos inactivos;
pide precisión cuando encuentra varias coincidencias similares;
deriva productos no encontrados;
deriva cotizaciones, descuentos, pedidos, compras, reclamos y solicitudes de asesor;
muestra en terminal el motivo de la derivación.


## Pasos completados
1. Crear la plantilla de Google Sheets.
2. Implementar y probar el servicio de catálogo sin IA.
3. Crear búsquedas por SKU, nombre y palabras clave.
4. Simular conversaciones desde una terminal.

## Siguientes pasos:
5. Incorporar el modelo únicamente para interpretar mensajes y redactar.
6. Agregar reglas de derivación. (aquí ya se tiene un avance preliminar, pero se puede mejorar)
7. Conectar el webhook de WhatsApp.
8. Desplegar el backend.
9. Probar conversaciones reales.
10. Agregar MCP como módulo demostrativo, no como dependencia central