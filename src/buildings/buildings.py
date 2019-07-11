#!/usr/bin/python
from enum import Enum, unique


from phases import Effect
from phases import Phase
from player import Player
from player import ColorPlayer
from moneyres import Money
from moneyres import MoneyResource
from moneyres import Resource


from game.utils import indent




class Building:
    """Buildings (cards)."""

    ABBREV_NO_USE_EFFECT = 'N'  # type: str[1]
    TXT_NO_USE_EFFECT = '(' + ABBREV_NO_USE_EFFECT + ' if you don\'t want to use the effect)'  # type: str

    game_element = None  # type: GameElement # Used for the church and lawyer player buildings.

    def __init__(self, belongs_to_beginner_version: bool, can_be_a_prestige_building: bool,
                 allows_to_place_a_worker: bool, front_color: str, name: str, n_prestige_pts: int,
                 primary_effect: Effect, resource_costs):
        """Initialization of a building."""
        self.belongs_to_beginner_version = belongs_to_beginner_version  # type: bool
        self.can_be_a_prestige_building = can_be_a_prestige_building  # type: bool
        self.allows_to_place_a_worker = allows_to_place_a_worker  # type: bool
        self.front_color = front_color  # type: str
        self.name = name  # type: str
        self.n_prestige_pts = n_prestige_pts  # type: int
        self.primary_effect = primary_effect  # type: Effect
        self.resource_costs = resource_costs  # type: Dict[Optional[Resource], int]

    def txt_name_owner(self, with_owner: bool) -> str:
        """Get the text of the name of the building with the owner."""
        return self.name + (' which belongs to ' + self.color_player.player.name()
                            if with_owner
                               and self.get_building_type() in [BuildingType.PLAYER, BuildingType.BACKGROUND,
                                                                BuildingType.PRESTIGE]
                               and self.color_player is not None else '')

    def income_effect(self, income_phase: Phase = None) -> None:
        """Give some money to the player owing the building on the road."""
        pass  # No money is given excepted for each résidence player building and the hotel prestige building along the road.

    def apply_no_cost_only_gain_effect(self, money_resources_gain, player: Player = None) -> None:
        """Apply the effect of a building for (the worker of) the player. This effect doesn't require any cost and give some gain; so, we don't ask it hte player want it and give him."""
        if player is None:
            player = self.color_player.player
        money_resource, qty = money_resources_gain  # type: Tuple[MoneyResource, int]
        player.current_money_resources[money_resource] += qty
        print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) + '.')

    def apply_peddler_effect(self, player: Player) -> None:
        """Apply the effect of a peddler (neutral or player) building."""
        """
        Buy 1 cube (any resource but gold) from the stock with 1 denier.
        """
        # Remark: Hard-coded! We don't use the tags <cost><n_deniers>-1 and <gain><CHOICES>... in <game_elements><buildings><player_buildings><player_building><secondary_effect>.
        money_resource_cost, qty_cost = Money.money, -1  # type: MoneyResource, int
        if player.current_money_resources[money_resource_cost] + \
                qty_cost < 0:  # Has the player enough money or resource?
            print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                  ' and can\'t apply the effect because he/she doesn\'t have enough money or resource as ' +
                  str(qty_cost) + ' ' + money_resource_cost.name + '(s) required.')
        else:
            resource_gain_choices, qty_gain = [resource for resource in Resource.resources.values()
                                               if not resource.is_wild()], \
                                              +1  # type: List[Resource], int
            resource_gain = player.choose_buy_resource(money_resource_cost, qty_cost, resource_gain_choices,
                                                       qty_gain)  # type: Resource
            if resource_gain is None:
                print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                      ' and had chosen to don\'t apply the effect.')
            else:
                print(indent(4) + player.name() + ' wants to consume ' + str(qty_cost) + ' ' +
                      money_resource_cost.name + '(s) to obtain ' + str(qty_gain) + ' ' + resource_gain.name + '(s).')
                player.current_money_resources[money_resource_cost] += qty_cost
                player.current_money_resources[resource_gain] += qty_gain
                print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                      ' once the effect applied.')

    def apply_effect_multi(self, player: Player, all_costs, resource_gain_choices, single_qty_gain: int) -> None:
        """Apply an effect with several choices (e.g. primary effects of bank and peddler player buildings)."""
        # :param all_costs:  # type: List[Tuple[Money, int]] # Must be ordered!
        # :param resource_gain_choices: # type: List[Resource]
        costs = [(money_resource_cost, qty_cost) for (money_resource_cost, qty_cost) in all_costs
                 if player.current_money_resources[money_resource_cost] + qty_cost >= 0]
        if not costs:  # Has the player enough money or resource?
            print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                  ' and can\'t apply the effect because he/she doesn\'t have enough money or resource as ' +
                  'either ' + ' or '.join(str(qty_cost) + ' ' + money_resource_cost.name + '(s)'
                                          for (money_resource_cost, qty_cost) in all_costs) + ' required.')
        elif len(costs) == 1:
            print(indent(4) + 'There exists only one choice according to money and resources you have.')
            money_resource_cost, qty_cost = costs[0]
            resource_gain = player.choose_buy_resource(money_resource_cost, qty_cost, resource_gain_choices,
                                                       single_qty_gain)  # type: Resource
            if resource_gain is None:
                print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                      ' and had chosen to don\'t apply the effect.')
            else:
                print(indent(4) + player.name() + ' wants to consume ' +
                      str(qty_cost) + ' ' + money_resource_cost.name + '(s) to obtain ' +
                      str(single_qty_gain) + ' ' + resource_gain.name + '(s).')
                player.current_money_resources[money_resource_cost] += qty_cost
                player.current_money_resources[resource_gain] += single_qty_gain
                print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                      ' once the effect applied.')
        else:
            resources_gain = player.choose_buy_resource_multi(costs, resource_gain_choices,
                                                              len(costs) * single_qty_gain)
            if not resources_gain:
                print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                      ' and had chosen to don\'t apply the effect.')
            else:
                money_resource_cost, qty_cost = costs[len(resources_gain) - 1]  # costs must be ordered!
                print(indent(4) + player.name() + ' wants to consume ' +
                      str(qty_cost) + ' ' + money_resource_cost.name + '(s).')
                player.current_money_resources[money_resource_cost] += qty_cost
                for resource_gain, qty_gain in collections.Counter(resources_gain).items():  # To group by resource.
                    print(indent(4) + player.name() + ' wants to obtain ' +
                          str(single_qty_gain * qty_gain) + ' ' + resource_gain.name + '(s).')
                    player.current_money_resources[resource_gain] += single_qty_gain * qty_gain
                print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                      ' once the effect applied.')



class BackgroundPlayerBuilding(Building):
    """Background of all the player buildings (green cards) corresponding to the résidence player building."""
    """
    Exists exactly one background player building for each color of player and conversely exists exactly one color of player for each background player building.
    So, each player has got exactly one background player building (for one color of player).
    Each player building transformed into a résidence refers to the same background player building.
    """

    def __init__(self, belongs_to_beginner_version: bool, can_be_a_prestige_building: bool,
                 allows_to_place_a_worker: bool, front_color: str, name: str, n_prestige_pts: int,
                 primary_effect: Effect, resource_costs, color_player: ColorPlayer = None):
        """Initialization of a background player building."""
        Building.__init__(self, belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                          front_color, name, n_prestige_pts, primary_effect, resource_costs)
        # Specific attributes.
        self.color_player = color_player  # type: ColorPlayer

    def get_building_type(self):  # -> BuildingType
        """Indicates that this building is a background player building."""
        return BuildingType.BACKGROUND

    def income_effect(self, income_phase: Phase = None) -> None:
        """Give some money to the player owing this background player building on the road."""
        n_deniers = income_phase.n_deniers_per_residence  # type: int
        print(indent(2) + self.color_player.player.name() + ' obtains ' + str(n_deniers) + ' ' + Money.money.name +
              '(s) for a(n) ' + self.name + ' building along the road.')
        self.color_player.player.current_money_resources[Money.money] += n_deniers


class NeutralBuilding(Building):
    """All 5 neutral buildings (pink cards): park, forest, quarry, peddler, trading post."""
    """
    Each neutral building is described by its name and effect (effect phase).
    """

    # belongs_to_beginner_version = None  # type: bool
    # front_color = None  # type: str
    # n_prestige_pts = 0  # type: int
    neutral_buildings = {}  # type: Dict[str, NeutralBuilding] # All neutral buildings where key is name and value is NeutralBuilding.

    def __init__(self, belongs_to_beginner_version: bool, can_be_a_prestige_building: bool,
                 allows_to_place_a_worker: bool, front_color: str, name: str, n_prestige_pts: int,
                 primary_effect: Effect, resource_costs=None):
        """Initialization of a neutral building."""
        # We have: belongs_to_beginner_version = None, front_color = None, n_prestige_pts = 0, resource_costs = None.
        Building.__init__(self, belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                          front_color, name, n_prestige_pts, primary_effect, resource_costs)
        NeutralBuilding.neutral_buildings[name] = self

    @staticmethod
    def get_neutral_building(name: str):  # -> NeutralBuilding
        """Get a neutral building from its name."""
        return NeutralBuilding.neutral_buildings.get(name)

    def get_building_type(self):  # -> BuildingType
        """Indicates that this building is a neutral building."""
        return BuildingType.NEUTRAL

    def apply_primary_effect(self, player: Player) -> None:
        """Apply the (default that is for park, forest, quarry and trading post) effect of a neutral building."""
        print(indent(3) + 'Effect of the neutral building ' + self.name +
              ' for a worker of the player ' + player.name() + ': ' + self.primary_effect.text)
        self.apply_no_cost_only_gain_effect(self.primary_effect.money_resources_gain, player)


class PeddlerNeutralBuilding(NeutralBuilding):
    """Peddler neutral building."""

    def __init__(self, belongs_to_beginner_version: bool, can_be_a_prestige_building: bool,
                 allows_to_place_a_worker: bool, front_color: str, name: str, n_prestige_pts: int,
                 primary_effect: Effect, resource_costs):
        """Initialization of a peddler neutral building."""
        NeutralBuilding.__init__(self, belongs_to_beginner_version, can_be_a_prestige_building,
                                 allows_to_place_a_worker, front_color, name, n_prestige_pts, primary_effect,
                                 resource_costs)

    def apply_primary_effect(self, player: Player) -> None:
        """Apply the effect of a peddler neutral building."""
        """
        Buy 1 cube (any resource but gold) from the stock with 1 denier.
        """
        # Remark: Hard-coded! We don't use the tags <cost><n_deniers>-1 and <gain><CHOICES>... in <game_elements><buildings><neutral_buildings><neutral_building>.
        print(indent(3) + 'Effect of the neutral building ' + self.name +
              ' for a worker of the player ' + player.name() + ': ' + self.primary_effect.text)
        self.apply_peddler_effect(player)


class PrestigeBuilding(Building):
    """All 7 prestige buildings (blue cards): theatre, statue, hotel, stables, town hall, monument, cathedral."""
    """
    Each prestige building is described by its name, cost (number of food, wood, stone or gold), number of prestige
    points and [optionally] effect (income phase).
    """

    # front_color = None  # type: str

    def __init__(self, belongs_to_beginner_version: bool, can_be_a_prestige_building: bool,
                 allows_to_place_a_worker: bool, front_color: str, name: str, n_prestige_pts: int,
                 primary_effect: Effect, resource_costs, color_player: ColorPlayer = None):
        """Initialization of a prestige building."""
        Building.__init__(self, belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                          front_color, name, n_prestige_pts, primary_effect, resource_costs)
        # Specific attributes.
        self.color_player = color_player  # type: ColorPlayer

    def get_building_type(self):  # -> BuildingType
        """Indicates that this building is a prestige building."""
        return BuildingType.PRESTIGE


class HotelPrestigeBuilding(PrestigeBuilding):
    """Hotel prestige building."""

    def __init__(self, belongs_to_beginner_version: bool, can_be_a_prestige_building: bool,
                 allows_to_place_a_worker: bool, front_color: str, name: str, n_prestige_pts: int,
                 primary_effect: Effect, resource_costs, color_player: ColorPlayer = None):
        """Initialization of an hotel prestige building."""
        PrestigeBuilding.__init__(self, belongs_to_beginner_version, can_be_a_prestige_building,
                                  allows_to_place_a_worker, front_color, name, n_prestige_pts, primary_effect,
                                  resource_costs, color_player)

    def income_effect(self, income_phase: Phase = None) -> None:
        """Give some money to the player owing this hotel prestige building on the road."""
        n_deniers = income_phase.n_deniers_if_hotel  # type: int
        print(indent(2) + self.color_player.player.name() + ' obtains ' + str(n_deniers) + ' ' + Money.money.name +
              '(s) for a(n) ' + self.name + ' building along the road.')
        self.color_player.player.current_money_resources[Money.money] += n_deniers


@unique
class BuildingType(Enum):
    """Enumeration of all the types of buildings."""
    """
    We choose to code the building type with an enumeration instead of using .__class__ or type() into Building classes.
    """
    PRESTIGE = 0
    NEUTRAL = 1
    BACKGROUND = 2
    PLAYER = 3
