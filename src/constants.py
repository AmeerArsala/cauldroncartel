RED = 0
BLUE = 1
GREEN = 2

ML_PER_BOTTLE = 100


def create_pure_potion(potion_type_index: int) -> list[int]:
    potion: list[int] = [0, 0, 0, 0]
    potion[potion_type_index] = ML_PER_BOTTLE

    return potion


PURE_RED_POTION = create_pure_potion(RED)
PURE_BLUE_POTION = create_pure_potion(BLUE)
PURE_GREEN_POTION = create_pure_potion(GREEN)
