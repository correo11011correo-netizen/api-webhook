# Repositorio de Arquitectura de Webhooks de Meta API

## 1. Arquitectura y Visión General

Este repositorio contiene la configuración y el código funcional para una arquitectura de webhooks desacoplada y robusta, diseñada para recibir y procesar webhooks de la API de Meta (WhatsApp, Instagram, etc.).

La arquitectura se divide en dos componentes principales:

1.  **Webhook Forwarder (Reenviador)**: Un servicio ligero y seguro expuesto a Internet que recibe las peticiones de Meta y las reenvía al "Bot Engine" activo.
2.  **Bot Engine (Motor del Bot)**: Uno o más servicios internos que contienen la lógica de negocio compleja del bot.

**Para una explicación detallada de la arquitectura, cómo replicar toda la configuración desde cero y cómo añadir nuevos bots, por favor, consulta nuestra guía completa:**

➡️ **[Guía Completa: Replicar y Expandir la Arquitectura de Webhooks](HOW_TO_REPLICATE.md)**

---

## 2. Información Clave del Proyecto

- **Proyecto Google Cloud (GCP)**: `My First Project` (ID: `project-2eb71890-6e93-4cfd-a00`)
- **Instancia de Cómputo (VM)**: `mi-servidor-web`
- **Endpoint Público del Webhook**: `https://api.fundacionidear.com/webhook`

---

## 3. Estructura del Repositorio

- **`/webhook-forwarder`**: Contiene el código y la configuración del servicio reenviador.
- **`/bot-engine`**: Contiene el código y la configuración del bot principal actual.
- **`/deployment-examples`**: Contiene plantillas para desplegar nuevos servicios.
- **`HOW_TO_REPLICATE.md`**: La guía de instalación y expansión completa.
- **`README.md`**: Este archivo.