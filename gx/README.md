# Diseño GX

La fuente de verdad ejecutable de reglas y metadata Rule ID está en `src/validation.py`. Se generan tres suites independientes: spotify_raw_suite, grammy_raw_suite y prepared_suite. No se necesita un contexto mutable compartido en disco: cada tarea crea un contexto efímero y persiste suite, resultado íntegro y política bajo su carpeta de run.

Suites y resultados de demostración: `docs/evidence/A_success/`, `B_critical_raw_failure/` y `C_safe_rerun/`. La tabla de reglas y umbrales está en `docs/04_quality_rules.md`.
