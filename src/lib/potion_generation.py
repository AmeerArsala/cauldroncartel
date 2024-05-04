from src.schemas.potions import Potion, PotionInventory
import src.constants as consts
import numpy as np


def generate_sku(red: int, blue: int, green: int, dark: int) -> str:
    names = ["RED", "BLUE", "GREEN", "DARK"]
    dominant_idx = np.argmax([red, blue, green, dark])

    dominant_name: str = names[dominant_idx]

    stats: str = f"R{red}B{blue}G{green}D{dark}"

    return f"{dominant_name}_POTION_{stats}"


def generate_sku_from_list(proportions: list[int]) -> str:
    return generate_sku(
        proportions[consts.RED],
        proportions[consts.BLUE],
        proportions[consts.GREEN],
        proportions[consts.DARK],
    )


def generate_potions(potions_inventory: list[PotionInventory]) -> list[Potion]:
    # Turn into a list of potions
    potion_list: list[Potion] = []
    for potion_inventory in potions_inventory:
        red_percent: int = potion_inventory.potion_type[consts.RED]
        blue_percent: int = potion_inventory.potion_type[consts.BLUE]
        green_percent: int = potion_inventory.potion_type[consts.GREEN]
        dark_percent: int = potion_inventory.potion_type[consts.DARK]

        quantity: int = potion_inventory.quantity

        sku: str = generate_sku(red_percent, blue_percent, green_percent, dark_percent)

        potion: Potion = Potion(
            sku=sku,
            red_percent=red_percent,
            blue_percent=blue_percent,
            green_percent=green_percent,
            dark_percent=dark_percent,
            quantity=quantity,
        )

        potion_list.append(potion)

    return potion_list


# NOTE: SUPER KEY ALGORITHM
# total_mls = np.array([red, blue, green, dark])
def make_potions_from_mls(total_mls: np.ndarray) -> list[Potion]:
    # Two Key decisions here:
    # 1: How much should be used
    # 2: Out of how much is being used, how should we choose to distribute what we make?

    # 1: Use as much as possible
    # 2: Just randomize it for now
    NUM_COLORS = 4

    made_potions: list[Potion] = []

    remaining_mls: np.ndarray = total_mls.copy()
    commission_states: np.ndarray = np.array([True, True, True, True])

    while True in (commission_states := (remaining_mls > consts.ML_PER_BOTTLE)):
        # Given an array of bools, make random discrete probabilities that sum to 1 for each one that is true (otherwise, 0.0)
        # Then multiply it by consts.ML_PER_BOTTLE and subtract it from `remaining_mls`

        # It only has scores with the ones it can 'afford'
        # Otherwise, the loop automatically ends
        random_scores = np.random.rand(NUM_COLORS) * commission_states

        # Normalize them
        random_probabilities = (random_scores / random_scores.sum()).round(2)
        random_percentages = (random_probabilities * 100).astype(int)

        mls_used = (random_probabilities * consts.ML_PER_BOTTLE).astype(int)

        # def relu(x: np.ndarray):
        #     return x * (x > 0)

        # Make a new Potion from this
        made_potions.append(
            Potion(
                sku=generate_sku_from_list(random_percentages),
                red_percent=random_percentages[consts.RED],
                blue_percent=random_percentages[consts.BLUE],
                green_percent=random_percentages[consts.GREEN],
                dark_percent=random_percentages[consts.DARK],
                quantity=1,
            )
        )

        # Subtract from remaining
        remaining_mls -= mls_used

    # used_up_mls: np.ndarray = total_mls - remaining_mls

    return made_potions
