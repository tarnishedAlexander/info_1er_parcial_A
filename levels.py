"""
Configuración de niveles para el juego Angry Birds
"""
from dataclasses import dataclass
from typing import List, Tuple

# Constantes del juego (importadas desde main)
WIDTH = 1800
HEIGHT = 800

@dataclass
class LevelData:
    """Estructura de datos para definir un nivel"""
    pigs: List[Tuple[float, float]]
    columns: List[Tuple[float, float]]
    description: str = ""
    max_birds: int = 3

def create_basic_level(pig_count: int, start_x: float = None) -> LevelData:
    """nivel básico con el número especificado de cerdos"""
    if start_x is None:
        start_x = WIDTH // 2
    
    pigs = []
    columns = []
    
    for i in range(pig_count):
        pig_x = start_x + (i * 200)
        pigs.append((pig_x, 100))
        
        # Agregar columnas alrededor de cada cerdo
        columns.append((pig_x - 50, 50))
        columns.append((pig_x + 50, 50))
    
    return LevelData(
        pigs=pigs,
        columns=columns,
        description=f"Nivel con {pig_count} cerdos",
        max_birds=min(pig_count + 1, 5)
    )

def create_tower_level(pig_positions: List[Tuple[float, float]]) -> LevelData:
    """Crea un nivel con torres alrededor de los cerdos"""
    columns = []
    
    for pig_x, pig_y in pig_positions:
        # Torre básica alrededor del cerdo
        tower_height = [50, 130, 210, 290]
        for height in tower_height:
            columns.append((pig_x - 30, height))
            columns.append((pig_x + 30, height))
    
    return LevelData(
        pigs=pig_positions,
        columns=columns,
        description="Nivel con torres defensivas",
        max_birds=len(pig_positions) + 2
    )

# Definición de niveles del juego (compatible con el código existente)
LEVELS = [
    # Nivel 1: Introducción
    {
        "pigs": [(WIDTH / 2, 100)],
        "columns": [(WIDTH // 2, 50), (WIDTH // 2 + 400, 50)],
        "description": "Nivel de introducción - Un cerdo fácil",
        "max_birds": 2
    },
    
    # Nivel 2: Dos objetivos
    {
        "pigs": [(WIDTH / 2, 100), (WIDTH / 2 + 200, 100)],
        "columns": [(WIDTH // 2, 50), (WIDTH // 2 + 200, 50), (WIDTH // 2 + 400, 50)],
        "description": "Dos cerdos para practicar",
        "max_birds": 3
    },
    
    # Nivel 3: Tres objetivos
    {
        "pigs": [(WIDTH / 2, 100), (WIDTH / 2 + 200, 100), (WIDTH / 2 + 400, 100)],
        "columns": [(WIDTH // 2, 50), (WIDTH // 2 + 200, 50), (WIDTH // 2 + 400, 50), (WIDTH // 2 + 600, 50)],
        "description": "Tres cerdos - aumenta la dificultad",
        "max_birds": 4
    },
    
    # Nivel 4: Torres defensivas
    {
        "pigs": [(WIDTH / 2, 100), (WIDTH / 2 + 300, 100)],
        "columns": [
            # Torres alrededor del primer cerdo
            (WIDTH / 2 - 30, 50), (WIDTH / 2 - 30, 130), (WIDTH / 2 - 30, 210),
            (WIDTH / 2 + 30, 50), (WIDTH / 2 + 30, 130), (WIDTH / 2 + 30, 210),
            # Torres alrededor del segundo cerdo  
            (WIDTH / 2 + 270, 50), (WIDTH / 2 + 270, 130),
            (WIDTH / 2 + 330, 50), (WIDTH / 2 + 330, 130)
        ],
        "description": "Torres defensivas - usa la catapulta",
        "max_birds": 4
    },
    
    # Nivel 5: Desafío final
    {
        "pigs": [
            (WIDTH / 2, 100), 
            (WIDTH / 2 + 200, 100), 
            (WIDTH / 2 + 400, 100),
            (WIDTH / 2 + 200, 200)  # Cerdo elevado
        ],
        "columns": [
            # Base
            (WIDTH // 2, 50), (WIDTH // 2 + 200, 50), (WIDTH // 2 + 400, 50),
            # Torre central
            (WIDTH // 2 + 200, 130), (WIDTH // 2 + 200, 210),
            # Protecciones laterales
            (WIDTH // 2 - 50, 50), (WIDTH // 2 + 450, 50),
            # Torres adicionales
            (WIDTH // 2 + 150, 50), (WIDTH // 2 + 250, 50)
        ],
        "description": "Nivel final - Torre con cerdo elevado",
        "max_birds": 6
    }
]

def get_level(level_index: int) -> dict:
    """Obtiene un nivel específico o el último si el índice es muy alto"""
    if level_index < len(LEVELS):
        return LEVELS[level_index]
    return LEVELS[-1]  # Retorna el último nivel si se pasa del límite

def get_total_levels() -> int:
    """Retorna el número total de niveles"""
    return len(LEVELS)
