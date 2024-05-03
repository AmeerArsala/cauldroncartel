from src.schemas.barrels import Barrels, BarrelSchema
from src import constants as consts
import numpy as np


def generate_sku(ml_per_barrel: int, red: int, blue: int, green: int, dark: int) -> str:
    # Colors
    names = ["RED", "BLUE", "GREEN", "DARK"]
    dominant_idx = np.argmax([red, blue, green, dark])

    dominant_color: str = names[dominant_idx]

    color_stats: str = f"R{red}B{blue}G{green}D{dark}"

    # Size
    barrel_size: str = ""
    if ml_per_barrel >= 10_000:
        barrel_size = "GIGANTIC XL DELUXE"
    elif ml_per_barrel >= 5000:
        barrel_size = "HUMONGOUS (Among Us)"
    elif ml_per_barrel >= 2500:
        barrel_size = "LARGE"
    elif ml_per_barrel >= 1250:
        barrel_size = "BIG"
    elif ml_per_barrel >= 1000:
        barrel_size = "MEDIUM"
    elif ml_per_barrel >= 500:
        barrel_size = "SMALL"
    else:
        barrel_size = "TINY"

    return f"{barrel_size}_{dominant_color}_BARREL_{color_stats}"


def generate_sku_from_list(ml_per_barrel: int, proportions: list[int]) -> str:
    return generate_sku(
        ml_per_barrel,
        proportions[consts.RED],
        proportions[consts.BLUE],
        proportions[consts.GREEN],
        proportions[consts.DARK],
    )


# Equalize barrels given the new ml
# Return a new set of barrels representing the updates that should be made to the barrels
# Maybe this is a good use-case for an ORM?
# NOTE: KEY ALGORITHM
def stabilize_barrels(new_total_ml: np.ndarray) -> list[BarrelSchema]:
    # Honestly, just collapse them into the largest possible barrels of each category (red, blue, green, dark)
    new_total_red_ml: int = new_total_ml[consts.RED]
    new_total_blue_ml: int = new_total_ml[consts.BLUE]
    new_total_green_ml: int = new_total_ml[consts.GREEN]
    new_total_dark_ml: int = new_total_ml[consts.DARK]

    barrel_schemas: list[BarrelSchema] = [
        # Red Barrel
        BarrelSchema(
            sku=generate_sku(new_total_red_ml, red=100, blue=0, green=0, dark=0),
            red_percent=100,
            blue_percent=0,
            green_percent=0,
            dark_percent=0,
            ml_per_barrel=new_total_red_ml,
            quantity=1,
        ),
        # Blue Barrel
        BarrelSchema(
            sku=generate_sku(new_total_blue_ml, red=0, blue=100, green=0, dark=0),
            red_percent=0,
            blue_percent=100,
            green_percent=0,
            dark_percent=0,
            ml_per_barrel=new_total_blue_ml,
            quantity=1,
        ),
        # Green Barrel
        BarrelSchema(
            sku=generate_sku(new_total_green_ml, red=0, blue=0, green=100, dark=0),
            red_percent=0,
            blue_percent=0,
            green_percent=100,
            dark_percent=0,
            ml_per_barrel=new_total_green_ml,
            quantity=1,
        ),
        # Dark Barrel
        BarrelSchema(
            sku=generate_sku(new_total_dark_ml, red=0, blue=0, green=0, dark=100),
            red_percent=0,
            blue_percent=0,
            green_percent=0,
            dark_percent=100,
            ml_per_barrel=new_total_dark_ml,
            quantity=1,
        ),
    ]

    return barrel_schemas
