# Desarrollo de un Gemelo Digital para un Electrolizador de Membrana de Intercambio de Protones (PEM)

Este proyecto permite desarrollar y simular un gemelo digital de un electrolizador de membrana de intercambio de protones (PEM). Puedes ejecutar el código utilizando Google Project IDX:

<a href="https://idx.google.com/import?url=https%3A%2F%2Fgithub.com%2Fsantiagoavilaunal%2FDigitalTwinElectrolizadorPEM">
  <img
    height="32"
    alt="Open in IDX"
    src="https://cdn.idx.dev/btn/open_light_32.svg">
</a>

## Objetivo

El objetivo principal de este proyecto es el desarrollo de un gemelo digital para un electrolizador de membrana de intercambio de protones (PEM). Este gemelo digital se ha desarrollado utilizando una metodología que incluye la creación de un simulador específico para considerar todos los fenómenos que pueden afectar el sistema.

## Metodología

- **Simulación Específica:** Se empleó el paquete termodinámico Coolprop para determinar las propiedades térmicas y de equilibrio de solubilidad, evitando simplificaciones idealizadas del sistema.
- **Ajuste de Parámetros:** Se ajustaron algunos parámetros de interacción binaria para modelar los equipos de separación de fase y se reajustaron los parámetros en el modelo de cinética electroquímica basándose en datos proporcionados por Espinosa y diversas fuentes bibliográficas.
- **Dimensionamiento de Equipos:** Se dimensionaron los equipos de separación de fases, como el intercambiador de calor.
- **Evaluación del Desempeño:** Se evaluó el desempeño del simulador en diversas condiciones mediante un análisis de sensibilidad en estado estacionario.
- **Control Dinámico:** Se exploró el uso de un controlador PID con el modelo dinámico.

## Interfaz Gráfica

Se diseñó una interfaz gráfica para el electrolizador utilizando principalmente Python. Esta interfaz permite una visualización intuitiva y una interacción efectiva con el gemelo digital desarrollado.
