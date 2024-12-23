# Proyecto de Título: DESARROLLO DE UN LLM PARA LA GENERACIÓN DE CÓDIGO DESDE HISTORIAS DE USUARIO Y DIAGRAMAS DE CLASE.

# Descripción General

Este proyecto tiene como objetivo principal la automatización de la generación de artefactos (historias de usuario, modelos UML y código asociado) para sistemas basados en microservicios en el dominio del comercio electrónico. Utilizando un enfoque orientado a datos y herramientas modernas, el sistema automatiza tareas críticas del desarrollo, desde la generación de requisitos hasta la implementación de prototipos funcionales.

### Objetivo General

Automatizar la generación de artefactos de software para microservicios, integrando modelos UML, historias de usuario y código en un sistema unificado que acelere el desarrollo y reduzca errores.

### Objetivos Específicos

1. **Integrar herramientas modernas de desarrollo**: Utilizar Python, Java con Spring Boot, Docker y Kubernetes para construir un ecosistema de desarrollo robusto.
2. **Generar un dataset estructurado**: Crear un conjunto de datos que combine historias de usuario, diagramas UML y código asociado para entrenar modelos de lenguaje.
3. **Automatizar la extracción y modelado**: Diseñar un pipeline que procese repositorios de código y genere artefactos consistentes y reutilizables.
4. **Validar la trazabilidad de artefactos**: Asegurar que los diagramas, historias y código generados estén alineados con los requisitos del sistema.

## Principales Actividades Realizadas

1. **Análisis de repositorios**: Identificación y selección de repositorios de código relevantes, con énfasis en microservicios escritos en Java utilizando Spring Boot.
2. **Desarrollo de scripts en Python**: Implementación de herramientas para la extracción de clases, generación de UML en PlantUML y creación de historias de usuario con el soporte de OpenAI API.
3. **Contenerización de servicios**: Uso de Docker para encapsular microservicios y Kubernetes para la orquestación de los mismos.
4. **Diseño de un pipeline automatizado**: Creación de un flujo de trabajo iterativo que conecta las historias de usuario con diagramas UML y código fuente funcional.
5. **Pruebas y validación**: Validación del sistema mediante pruebas unitarias y de integración, utilizando bases de datos H2 y MySQL.

## Tecnologías Utilizadas

- **Python**: Para la automatización de la generación del dataset y manipulación de datos.
- **Google Colab**: Entorno para ejecutar scripts y generar artefactos en la nube.
- **Java (Spring Boot)**: Desarrollo de los microservicios que modelan el sistema de comercio electrónico.
- **H2 y MySQL**: Bases de datos utilizadas para pruebas (H2) y entornos de producción (MySQL).
- **Docker y Kubernetes**: Para contenerización y orquestación de los microservicios.
- **Elasticsearch Stack**: Monitoreo centralizado del sistema mediante logs y visualizaciones.
- **PlantUML**: Generación automática de diagramas UML basados en modelos extraídos de los microservicios.
- **TDD (Test-Driven Development)**: Enfoque de desarrollo para garantizar calidad desde las primeras etapas.

## Resultados Obtenidos

- **Dataset estructurado**: Un JSON que combina historias de usuario, diagramas UML y código funcional.
- **Pipeline automatizado**: Sistema que genera artefactos reutilizables a partir de entradas textuales y código fuente.
- **Validación de microservicios**: Diagramas y prototipos alineados con los requisitos iniciales.
- **Prototipo funcional**: Sistema navegable basado en los microservicios generados y modelados automáticamente.

## Estructura del Proyecto

1. **`/scripts`**: Contiene scripts en Python para la generación de artefactos.
2. **`/microservices`**: Directorio que alberga los microservicios desarrollados en Spring Boot.
3. **`/docker`**: Configuración de Docker para la contenerización de servicios.
4. **`/kubernetes`**: Archivos de configuración para la orquestación de Kubernetes.
5. **`/datasets`**: Dataset generado en formato JSON, combinando UML, historias de usuario y código.

## Cómo Ejecutar el Proyecto

1. **Clonar el repositorio**:
   ```bash
   git clone <url-del-repositorio>
   ```
2. **Generar el Dataset**:
   - Abrir el archivo de script en Google Colab o un entorno local.
   - Configurar las rutas al repositorio y ejecutar el script.
3. **Levantar los Microservicios**:
   - Usar Docker para contenerización:
     ```bash
     docker-compose up
     ```
   - Configurar Kubernetes para orquestación.
4. **Monitorear Logs y Métricas**:
   - Iniciar la pila ELK (Elasticsearch, Logstash y Kibana) para monitoreo.

## Conclusiones

El proyecto demuestra que la automatización de la generación de artefactos en sistemas basados en microservicios es viable y eficiente, reduciendo significativamente el tiempo y esfuerzo necesarios para la documentación y desarrollo. La integración de tecnologías modernas asegura la escalabilidad, trazabilidad y consistencia en proyectos complejos.

## Contacto

**Nombre del Autor**: Max Espindola\
**Correo**: [maxespindola@example.com](mailto:maxespindola@example.com)\
**Repositorio del Proyecto**: [URL del Repositorio]

## Getting started

To make it easy for you to get started with GitLab, here's a list of recommended next steps.

Already a pro? Just edit this README.md and make it your own. Want to make it easy? [Use the template at the bottom](#editing-this-readme)!

## Add your files

- [ ] [Create](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#create-a-file) or [upload](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#upload-a-file) files
- [ ] [Add files using the command line](https://docs.gitlab.com/ee/gitlab-basics/add-file.html#add-a-file-using-the-command-line) or push an existing Git repository with the following command:

```
cd existing_repo
git remote add origin https://gitlab.com/max0101/seminario-de-titulo.git
git branch -M main
git push -uf origin main
```

## Integrate with your tools

- [ ] [Set up project integrations](https://gitlab.com/max0101/seminario-de-titulo/-/settings/integrations)

## Collaborate with your team

- [ ] [Invite team members and collaborators](https://docs.gitlab.com/ee/user/project/members/)
- [ ] [Create a new merge request](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html)
- [ ] [Automatically close issues from merge requests](https://docs.gitlab.com/ee/user/project/issues/managing_issues.html#closing-issues-automatically)
- [ ] [Enable merge request approvals](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/)
- [ ] [Set auto-merge](https://docs.gitlab.com/ee/user/project/merge_requests/merge_when_pipeline_succeeds.html)

## Test and Deploy

Use the built-in continuous integration in GitLab.

- [ ] [Get started with GitLab CI/CD](https://docs.gitlab.com/ee/ci/quick_start/index.html)
- [ ] [Analyze your code for known vulnerabilities with Static Application Security Testing (SAST)](https://docs.gitlab.com/ee/user/application_security/sast/)
- [ ] [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/ee/topics/autodevops/requirements.html)
- [ ] [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/ee/user/clusters/agent/)
- [ ] [Set up protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html)

---

# Editing this README

When you're ready to make this README your own, just edit this file and use the handy template below (or feel free to structure it however you want - this is just a starting point!). Thanks to [makeareadme.com](https://www.makeareadme.com/) for this template.

## Suggestions for a good README

Every project is different, so consider which of these sections apply to yours. The sections used in the template are suggestions for most open source projects. Also keep in mind that while a README can be too long and detailed, too long is better than too short. If you think your README is too long, consider utilizing another form of documentation rather than cutting out information.

## Name

Choose a self-explaining name for your project.

## Description

Let people know what your project can do specifically. Provide context and add a link to any reference visitors might be unfamiliar with. A list of Features or a Background subsection can also be added here. If there are alternatives to your project, this is a good place to list differentiating factors.

## Badges

On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.

## Visuals

Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

## Installation

Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.

## Usage

Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Support

Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.

## Roadmap

If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributing

State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment

Show your appreciation to those who have contributed to the project.

## License

For open source projects, say how it is licensed.

## Project status

If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
