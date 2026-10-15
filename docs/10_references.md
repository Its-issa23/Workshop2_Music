# Referencias técnicas

Requisitos funcionales: documento adjunto del curso *Workshop-2: Building a Reliable Batch Data Pipeline*. Datasets: archivos Spotify y Grammy entregados en `sources/`, identificados mediante SHA256 en el perfilado.

- Apache Airflow 3.1.8, despliegue Docker: https://airflow.apache.org/docs/apache-airflow/3.1.8/howto/docker-compose/index.html
- Apache Airflow, Task SDK: https://airflow.apache.org/docs/task-sdk/stable/index.html
- Great Expectations, DataFrames y ValidationDefinition: https://docs.greatexpectations.io/docs/core/connect_to_data/dataframes/
- Great Expectations, ValidationDefinition API: https://docs.greatexpectations.io/docs/reference/api/validationdefinition_class/
- Microsoft, Power BI Projects: https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview
- Microsoft, formato PBIR: https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report
- Microsoft, modelo semántico PBIP: https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset
- Esquemas oficiales PBIR: https://github.com/microsoft/json-schemas/tree/main/fabric/item/report

La implementación GX está fijada y ejecutada con 1.8.1; la documentación web puede describir una versión posterior. Las pruebas locales, no la mera compatibilidad documental, sustentan el resultado de ejecución.
