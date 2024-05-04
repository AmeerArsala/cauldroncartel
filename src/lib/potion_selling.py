from src.schemas.potions import Potion
from src import constants as consts
import numpy as np
import random


# Will also need information on what's already on sale
# NOTE: SUPER KEY ALGORITHM
def put_subset_for_sale(potions: list[Potion]) -> list[Potion]:
    # For now just choose 6 random ones
    CATALOG_LENGTH = 6

    if len(potions) > CATALOG_LENGTH:
        potions_for_sale: list[Potion] = np.random.choice(
            potions, size=CATALOG_LENGTH, replace=False
        ).tolist()

        return potions_for_sale
    else:
        return potions


def name_potion(potion: Potion) -> str:
    return f"{random.choice(consts.POTION_FIRST_NAMES)} {random.choice(consts.POTION_SECOND_NAMES)}"


# TODO: make this better
# NOTE: SUPER KEY ALGORITHM
def price_potion(potion: Potion) -> int:
    red_percentage: float = potion.red_percent / 100.0
    blue_percentage: float = potion.blue_percent / 100.0
    green_percentage: float = potion.green_percent / 100.0
    dark_percentage: float = potion.dark_percent / 100.0

    # For now, let's assume a linear regression occurred and set some coefficients

    # A purely red potion costs...
    full_red = 100

    # A purely blue potion costs...
    full_blue = 200

    # A purely green potion costs...
    full_green = 200

    # A purely dark potion costs...
    full_dark = 500

    # Time for a linear combination!!!
    price = np.dot(
        [red_percentage, blue_percentage, green_percentage, dark_percentage],
        [full_red, full_blue, full_green, full_dark],
    )

    return price
