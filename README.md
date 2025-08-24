# Angry Birds - Garabato Edition

Un juego de Angry Birds mejorado que combina el clásico sistema de resortera con una innovadora catapulta dibujable.

## Controles

- **Click y Arrastra**: Apuntar en modo resortera
- **C**: Cambiar entre modo resortera y catapulta
- **1-3**: Seleccionar tipo de pájaro (Rojo, Amarillo, Azul)
- **SPACE**: Activar habilidad especial del pájaro
- **R**: Reiniciar nivel actual
- **ESC**: Salir del juego (mantener 5 segundos)

## Modo garabato

Lastimosamente no funciona como deberia.

## Modo Catapulta

1. **Primer Click**: Cargar pájaro en la catapulta
2. **Arrastrar Mouse**: Dibujar la rampa personalizada
3. **Click Final**: Elegir punto de caída del pájaro

## Tipos de Pájaros

- **Rojo**: Pájaro básico, bueno para derribar estructuras
- **Amarillo**: Acelera durante el vuelo con SPACE
- **Azul**: Se divide en 3 pájaros con SPACE

## Ejecutar

```bash
python main.py
```

## Archivos del Proyecto

- `main.py` - Archivo principal del juego
- `game_object.py` - Clases de pájaros, cerdos y obstáculos
- `game_logic.py` - Lógica de física y matemáticas
- `catapult.py` - Sistema de catapulta personalizable
- `levels.py` - Configuración de niveles
- `assets/` - Recursos gráficos
