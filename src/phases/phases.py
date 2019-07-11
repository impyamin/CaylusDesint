class Phase:
    """All 6 phases of a turn."""

    def __init__(self, belongs_to_beginner_version: bool, numero: int, name: str):
        """Initialization of a phase."""
        # Attributes obtained from the XML file.
        self.belongs_to_beginner_version = belongs_to_beginner_version  # type: bool
        self.numero = numero  # type: int
        self.name = name  # type: str


class IncomePhase:
    """Collecting income phase."""

    def __init__(self, belongs_to_beginner_version: bool, numero: int, name: str, n_deniers: int,
                 n_deniers_per_residence: int, n_deniers_if_hotel: int):
        """Initialization of the collecting income phase."""
        Phase.__init__(self, belongs_to_beginner_version, numero, name)
        # Specific attributes.
        self.n_deniers = n_deniers  # type: int
        self.n_deniers_per_residence = n_deniers_per_residence  # type: int
        self.n_deniers_if_hotel = n_deniers_if_hotel  # type: int


class ActionsPhase:
    """Phase of actions."""

    def __init__(self, belongs_to_beginner_version: bool, numero: int, name: str, n_deniers_to_take_a_card: int,
                 n_deniers_to_discard_all_cards: int, n_deniers_to_place_a_worker: int, n_workers: int,
                 n_deniers_for_first_player_passing: int):
        """Initialization of the phase of actions."""
        Phase.__init__(self, belongs_to_beginner_version, numero, name)
        # Specific attributes.
        self.n_deniers_to_take_a_card = n_deniers_to_take_a_card  # type: int # The player pays 1 denier to the stock to take the first card on their pile and add it to their hand.
        self.n_deniers_to_discard_all_cards = n_deniers_to_discard_all_cards  # type: int # The player pays 1 denier to the stock to discard all the cards in their hand.
        self.n_deniers_to_place_a_worker = n_deniers_to_place_a_worker  # type: int # The player pays 1 denier to the stock and ...
        self.n_workers = n_workers  # type: int # ... places 1 worker on a card along the road.
        self.n_deniers_for_first_player_passing = n_deniers_for_first_player_passing  # type: int # The player puts their passing marker on the space of the bridge with the lowest number. The first player who passes gets 1 denier from the stock.


class ProvostMovementPhase:
    """Provost’s movement phase."""

    def __init__(self, belongs_to_beginner_version: bool, numero: int, name: str, n_turns_to_move_provost: int,
                 n_deniers_per_a_provost_movement: int, n_max_provost_movements_per_player: int):
        """Initialization of the Provost’s movement phase."""
        Phase.__init__(self, belongs_to_beginner_version, numero, name)
        # Specific attributes.
        self.n_turns_to_move_provost = n_turns_to_move_provost  # type: int
        self.n_deniers_per_a_provost_movement = n_deniers_per_a_provost_movement  # type: int
        self.n_max_provost_movements_per_player = n_max_provost_movements_per_player  # type: int


class EffectsBuildingsPhase:
    """Phase of the effects of the buildings."""

    def __init__(self, belongs_to_beginner_version: bool, numero: int, name: str):
        """Initialization of the phase of the effects of the buildings."""
        Phase.__init__(self, belongs_to_beginner_version, numero, name)


class CastlePhase:
    """Castle phase."""

    def __init__(self, belongs_to_beginner_version: bool, numero: int, name: str,
                 n_gold_cubes_for_player_offered_most_batches: int, n_prestige_pt_tokens_to_remove: int,
                 resource_costs):
        """Initialization of the castle phase."""
        Phase.__init__(self, belongs_to_beginner_version, numero, name)
        # Specific attributes.
        self.n_gold_cubes_for_player_offered_most_batches = n_gold_cubes_for_player_offered_most_batches  # type: int # The player who has offered the most batches during this phase takes 1 gold cube from the stock. In case of a draw, the player who offered that number of batches first wins the cube.
        self.n_prestige_pt_tokens_to_remove = n_prestige_pt_tokens_to_remove  # type: int # If no-one has offered any batch during this phase, 2 tokens are removed from the stock of victory points - these tokens are removed from the game.
        self.resource_costs = resource_costs  # type: Dict[Resource, int] # Cost of one batch.


class EndTurnPhase:
    """End turn phase."""

    def __init__(self, belongs_to_beginner_version: bool, numero: int, name: str, n_provost_advances: int):
        """Initialization of the end turn phase."""
        Phase.__init__(self, belongs_to_beginner_version, numero, name)
        # Specific attributes.
        self.n_provost_advances = n_provost_advances  # type: int # The Provost advances by 2 cards toward the end of the road. If there is only 1 card before the end of the road, the Provost only advances by 1 card. If the Provost is already at the end of the road, the Provost does not move.

class Effect:
    """Effect (primary or secondary) of a building."""

    def __init__(self, text: str, phase: Phase, money_resources_cost=None, money_resources_gain=None):
        """Initialization of an effect of a building."""
        self.text = text  # type: str
        self.phase = phase  # type: Phase
        self.money_resources_cost = money_resources_cost  # unused
        self.money_resources_gain = money_resources_gain  # type: Tuple[MoneyResource, int]
