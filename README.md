# Aureliano — Factored AI & Data Hackathon 2026

Sistema de atención al cliente bancario AI-first para el workflow de **información y elegibilidad de crédito**, construido sobre el dataset LATAM Bank.

> En construcción. Deadline: 2026-10-05, 23:59. Plan de trabajo: [docs/PLAN.md](docs/PLAN.md).

## Principios
- El LLM conversa; los números los calcula código determinista y cada cifra se verifica contra el output de una herramienta.
- Riesgo predictivo (modelo aprendido) y política de elegibilidad (reglas versionadas) están separados de la conversación.
- Permisos y autenticación se aplican en la capa de servicio, no en el prompt.
- Ante duda, datos faltantes o casos borderline: handoff estructurado a un humano.

## Código reutilizado
Algunas piezas genéricas (motor de amortización, audit log append-only, cliente LLM) provienen de un proyecto previo del equipo y se declaran explícitamente aquí cuando se incorporen.

## Setup
Copia `.env.example` a `.env` y completa las variables. **Nunca** subas credenciales al repositorio.
