# Plan — Equipo Aureliano

**Entrega:** 2026-10-05, 23:59 → enviar a hackathon.admin@factored.ai: repo público, link al deploy, 4-6 slides, video.
**Workflow elegido:** información y elegibilidad de productos de crédito.

## Arquitectura: Sistema 1 / Sistema 2

| Capa | Responsable | Qué decide |
|---|---|---|
| Sistema 1 (decisiones rápidas) | Jev (TypeSafe AI) | Intención, fuera de alcance, prompt injection, ¿escalar a humano? |
| Sistema 2 (conversación) | Claude Sonnet 5.5 | Redacta respuestas; **nunca** calcula ni inventa cifras |
| Riesgo predictivo | Modelo propio (p. ej. LightGBM) | Probabilidad de mora, con explicación por variable |
| Política de elegibilidad | Reglas deterministas versionadas | Elegible / no elegible / revisión humana |
| Verificador | Código | Toda cifra de la respuesta debe existir en el output de una tool con su ID de registro; si no, se bloquea y se escala |

Permisos y autenticación se aplican en la capa de tools (el cliente autenticado solo ve sus registros), no en el prompt.

## Datos (LATAM Bank, S3)
- Tablas: customers, products, transactions, call_center_interactions, call_transcripts, complaints, **digital_events**.
- `digital_events`: señales de fricción previas al contacto (errores, logins fallidos, abandono de formularios) como features, y señales de riesgo de sesión (IP de otro país) para step-up auth o escalar.
- Procesamiento con DuckDB; contratos de esquema, deduplicación (~2%), nulos (~5%), huérfanos y late arrivals documentados.

## Componentes aprendidos vs. baseline
1. **Riesgo de mora:** features en el snapshot mensual *t*, etiqueta `days_past_due > 30` en *t+3*. Split por cliente y por tiempo. Baseline: `credit_score` / tabla de puntos.
   - Plan B si el día 1 no hay señal: predictor de escalamiento (`was_escalated` / `was_resolved`) vs. regla fija.
2. **Decisiones de Sistema 1:** Jev vs. baseline de keywords vs. clasificador propio, en precisión, latencia y costo, sobre held-out.

Auditoría de leakage: lista de features descartadas y por qué (va a una slide).

## Evaluación (scoreboard)
- ~60 escenarios guionizados **ES + PT**: normal, ambiguo/no soportado, requiere humano, prompt injection, sesión expirada, fallo de tool, datos faltantes.
- Métricas de las reglas, con denominadores: safe automated resolution, containment, escalation quality, unsafe outcomes, latencia p50/p95, costo por caso; desagregadas por idioma y segmento.
- Haiku 4.5 para corridas masivas; Sonnet 5.5 para la corrida final del scoreboard.

## Stack
- Backend: Python + FastAPI.
- Frontend: Astro + isla React con shadcn/ui (chat + scoreboard), deploy en Vercel.
- Piezas reutilizadas del proyecto previo del equipo (declaradas en el README): amortización, audit log append-only, cliente LLM.

## Cronograma
| Días | Nicolás (DS/ML) | Compañero |
|---|---|---|
| 1 | Chequeo de señal y leakage; definir etiqueta | Portar piezas genéricas; probar Jev en ES/PT |
| 2-3 | Pipeline de datos con contratos + modelo vs. baseline | Agente, tools, política determinista, auth de prueba |
| 4-5 | Banco de escenarios ES/PT + métricas | Verificador de cifras, handoff JSON, frontend, deploy |
| 6 | Congelar deploy; scoreboard | README y documentación |
| 7 | Slides + video con guion (incluye fallos) | Enviar antes de las 23:59 |

## Pendientes
- [ ] Preguntar a los organizadores si se permite código previo (y la zona horaria del cierre).
- [ ] Pedir acceso a Jev en console.typesafe.ai.
- [ ] Credenciales del bucket S3 en `.env` local (nunca en el repo).
- [ ] Confirmar que `products` trae snapshots mensuales (condición del modelo de riesgo).
