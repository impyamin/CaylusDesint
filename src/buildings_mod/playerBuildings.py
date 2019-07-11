#!/usr/bin/python

from buildings_mod import *
import collections


from phases_mod import *
from player_mod import *

from moneyres_mod import *
from game_mod import *

from game_mod.utils import indent
from game_mod.utils import TXT_SEPARATOR
from game_mod.utils import Location

def ColorPlayer():
    pass
def Player():
    pass


class PlayerBuilding(Building):
    """A set per player of all 12 player buildings (cards of the color of the player): small farm, small sawmill,
    small quarry, peddler, market, lawyer, large farm, large sawmill, large quarry, gold mine, bank, church."""
    """
    Each player building is described by its front color, name, cost (number of food, wood, stone or of any type),
    number of prestige points, [optionally] construction (actions phase), primary and secondary effect (effect phase).
    """

    def __init__(self, belongs_to_beginner_version: bool, can_be_a_prestige_building: bool,
                 allows_to_place_a_worker: bool, front_color: str, name: str, n_prestige_pts: int,
                 primary_effect: Effect, resource_costs, can_be_a_residential_building: bool, secondary_effect: Effect,
                 color_player: ColorPlayer):
        """Initialization of a player building."""
        Building.__init__(self, belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                          front_color, name, n_prestige_pts, primary_effect, resource_costs)
        # Specific attributes.
        self.can_be_a_residential_building = can_be_a_residential_building  # type: bool
        self.secondary_effect = secondary_effect  # type: Effect
        self.color_player = color_player  # type: ColorPlayer

    def get_building_type(self):  # -> BuildingType
        """Indicates that this building is a player building."""
        return BuildingType.PLAYER

    def apply_primary_effect(self, player: Player) -> None:
        """Apply the (default) primary effect of a player building."""
        print(indent(3) + 'Primary effect of the player building ' + self.txt_name_owner(True) +
              ' for a worker of the player ' + player.name() + ': ' + self.primary_effect.text)
        pass  # Nothing to do!

    def apply_secondary_effect(self) -> None:
        """Apply the (default) secondary effect of a player building."""
        print(indent(3) + 'Secondary effect of the player building ' + self.txt_name_owner(True) + ': ' +
              self.secondary_effect.text)
        pass  # Nothing to do!


class SmallProductionPlayerBuilding(PlayerBuilding):
    """Small farm/sawmill/quarry (with construction) production of food/wood/stone player building."""

    def __init__(self, belongs_to_beginner_version: bool, can_be_a_prestige_building: bool,
                 allows_to_place_a_worker: bool, front_color: str, name: str, n_prestige_pts: int,
                 primary_effect: Effect, resource_costs, can_be_a_residential_building: bool, secondary_effect: Effect,
                 color_player: ColorPlayer, resource: Resource, n_cubes_into_area):
        """Initialization of a small production player building."""
        PlayerBuilding.__init__(self, belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                                front_color, name, n_prestige_pts, primary_effect, resource_costs,
                                can_be_a_residential_building, secondary_effect, color_player)
        # Specific attributes.
        self.resource = resource  # type: Resource
        self.n_cubes_into_area = n_cubes_into_area  # type: List[int]
        # Attributes to play a game.
        self.current_n_cubes_into_area = None  # type: int

    def setup(self, n_players: int) -> None:
        """Setup this small production player building."""
        self.current_n_cubes_into_area = self.n_cubes_into_area[n_players]

    def apply_primary_effect(self, player: Player) -> None:
        """Apply the primary effect of this small production player building."""
        super().apply_primary_effect(player)
        self.apply_no_cost_only_gain_effect(self.primary_effect.money_resources_gain, player)

    def apply_secondary_effect(self) -> None:
        """Apply the secondary effect of this small production player building."""
        super().apply_secondary_effect()
        if self.current_n_cubes_into_area == 0:
            print(indent(4) + 'There is no cube left in this small production player building, the owner gets nothing.')
        else:
            self.current_n_cubes_into_area -= 1
            print(indent(4) + 'There is now ' + str(self.current_n_cubes_into_area) +
                  ' cube(s) into the area of this small production player building.')
            self.apply_no_cost_only_gain_effect(self.secondary_effect.money_resources_gain, self.color_player.player)


class LargeProductionPlayerBuilding(PlayerBuilding):
    """Large farm/sawmill/quarry production of food/wood/stone player building."""

    def __init__(self, belongs_to_beginner_version: bool, can_be_a_prestige_building: bool,
                 allows_to_place_a_worker: bool, front_color: str, name: str, n_prestige_pts: int,
                 primary_effect: Effect, resource_costs, can_be_a_residential_building: bool, secondary_effect: Effect,
                 color_player: ColorPlayer, resource: Resource):
        """Initialization of a large production player building."""
        PlayerBuilding.__init__(self, belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                                front_color, name, n_prestige_pts, primary_effect, resource_costs,
                                can_be_a_residential_building, secondary_effect, color_player)
        # Specific attributes.
        self.resource = resource  # type: Resource

    def apply_primary_effect(self, player: Player) -> None:
        """Apply the primary effect of this large production player building."""
        super().apply_primary_effect(player)
        self.apply_no_cost_only_gain_effect(self.primary_effect.money_resources_gain, player)

    def apply_secondary_effect(self) -> None:
        """Apply the secondary effect of this large production player building."""
        super().apply_secondary_effect()
        self.apply_no_cost_only_gain_effect(self.secondary_effect.money_resources_gain, self.color_player.player)


class LawyerPlayerBuilding(PlayerBuilding):
    """Lawyer player building."""

    def __init__(self, belongs_to_beginner_version: bool, can_be_a_prestige_building: bool,
                 allows_to_place_a_worker: bool, front_color: str, name: str, n_prestige_pts: int,
                 primary_effect: Effect, resource_costs, can_be_a_residential_building: bool, secondary_effect: Effect,
                 color_player: ColorPlayer, n_residence_to_construct: int):
        """Initialization of a lawyer player building."""
        PlayerBuilding.__init__(self, belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                                front_color, name, n_prestige_pts, primary_effect, resource_costs,
                                can_be_a_residential_building, secondary_effect, color_player)
        # Specific attributes.
        self.n_residence_to_construct = n_residence_to_construct  # type: int

    def apply_primary_effect(self, player: Player) -> None:
        """Apply the primary effect of a lawyer player building."""
        """
        Construct a residential building by paying 1 food cube and turning over one of your cards along the road (except a Lawyer).
        """
        # Remark: Hard-coded! We don't use the tags <cost><n_food_cubes>-1 and <gain><n_residence_to_construct>+1 AND algorithm... in <game_elements><buildings><player_buildings><player_building><primary_effect>.
        super().apply_primary_effect(player)
        print(indent(4) + 'The road consists in: ' + self.game_element.game.txt_road(False) + '.')
        resource_cost, qty_cost = Resource.get_resource('food'), -1  # type: Resource, int
        if player.current_money_resources[resource_cost] + \
                player.current_money_resources[Resource.get_wild_resource()] + qty_cost < 0:
            print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                  ' and can\'t apply the effect because he/she doesn\'t have enough resource as ' +
                  str(qty_cost) + ' ' + resource_cost.name + '(s) required (even by considering wild resource).')
        else:
            i_road_buildings_on_road = [(i_road, building_worker[0])
                                        for (i_road, building_worker) in enumerate(self.game_element.game.road)
                                        if building_worker[0].get_building_type() == BuildingType.PLAYER
                                        and building_worker[0].color_player.player == player and
                                        building_worker[0].can_be_a_residential_building
                                        ]  # type: List[Tuple[PlayerBuilding]]
            if not i_road_buildings_on_road:
                print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                      ' and can\'t apply the effect because he/she has no building to be constructed as a residential building along the road.')
            else:
                resource_costs = None  # type: List[Tuple[Resource, int]]
                qty_current_resource_cost = player.current_money_resources[resource_cost]
                if qty_current_resource_cost == 0:
                    resource_costs = [(Resource.get_wild_resource(), qty_cost)]
                elif qty_current_resource_cost >= abs(qty_cost):
                    resource_costs = [(resource_cost, qty_cost)]
                else:
                    resource_costs = [(resource_cost, -qty_current_resource_cost),
                                      (Resource.get_wild_resource(), qty_cost + qty_current_resource_cost)]
                i_road_building_to_construct_as_residence = player.choose_construct_residence(resource_costs,
                                                                                              i_road_buildings_on_road)
                if i_road_building_to_construct_as_residence is None:
                    print(indent(4) +
                          player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                          ' and had chosen to don\'t apply the effect.')
                else:
                    i_road = i_road_building_to_construct_as_residence[0]  # type: int
                    building_to_construct_as_residence = i_road_building_to_construct_as_residence[
                        1]  # type: PlayerBuilding
                    print(indent(4) + player.name() + ' wants to consume ' +
                          ' and '.join(str(qty_cost) + ' ' + resource_cost.name + '(s)'
                                       for (resource_cost, qty_cost) in resource_costs) +
                          ' to construct his/her ' + i_road_building_to_construct_as_residence[1].name +
                          ' building (the ' + ordinal_number(i_road + 1) +
                          ' building along the road) as a residential building.')
                    for (resource_cost, qty_cost) in resource_costs:
                        player.current_money_resources[resource_cost] += qty_cost
                    if self.game_element.game.road[i_road][1] is not None:
                        # Remark: building_to_construct_as_residence is equals to self.game_element.game.road[i_road][0].
                        self.game_element.game.road[i_road].append(building_to_construct_as_residence)
                    self.game_element.game.road[i_road][0] = player.get_residence_building()
                    player.deck[building_to_construct_as_residence] = Location.REPLACED
                    print(indent(4) + 'The road consists in: ' + self.game_element.game.txt_road(False) + '.')
                    print(indent(4) +
                          player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                          ' once the effect applied.')

    def apply_secondary_effect(self) -> None:
        """Apply the secondary effect of a lawyer player building."""
        super().apply_secondary_effect()
        self.apply_no_cost_only_gain_effect(self.secondary_effect.money_resources_gain, self.color_player.player)


class PeddlerPlayerBuilding(PlayerBuilding):
    """Peddler player building."""

    def __init__(self, belongs_to_beginner_version: bool, can_be_a_prestige_building: bool,
                 allows_to_place_a_worker: bool, front_color: str, name: str, n_prestige_pts: int,
                 primary_effect: Effect, resource_costs, can_be_a_residential_building: bool, secondary_effect: Effect,
                 color_player: ColorPlayer):
        """Initialization of a peddler player building."""
        PlayerBuilding.__init__(self, belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                                front_color, name, n_prestige_pts, primary_effect, resource_costs,
                                can_be_a_residential_building, secondary_effect, color_player)

    def apply_primary_effect(self, player: Player) -> None:
        """Apply the primary effect of a peddler player building."""
        """
        Buy 1 or 2 cubes (any resource but gold) from the stock with 1 or 2 deniers.
        """
        # Remark: Hard-coded! We don't use the tag <CHOICES>... in <game_elements><buildings><player_buildings><player_building><secondary_effect>.
        super().apply_primary_effect(player)
        all_costs = [(Money.money, -1), (Money.money, -2)]  # type: List[Tuple[Money, int]] # Ordered!
        resource_gain_choices, single_qty_gain = [resource for resource in Resource.resources.values()
                                                  if not resource.is_wild()], \
                                                 +1  # type: List[Resource], int # single_qty_gain must be equals to one!
        self.apply_effect_multi(player, all_costs, resource_gain_choices, single_qty_gain)

    def apply_secondary_effect(self) -> None:
        """Apply the secondary effect of a peddler player building."""
        """
        Buy 1 cube (any resource but gold) from the stock with 1 denier.
        """
        # Remark: Hard-coded! We don't use the tags <cost><n_deniers>-1 and <gain><CHOICES>... in <game_elements><buildings><player_buildings><player_building><secondary_effect>.
        super().apply_secondary_effect()
        self.apply_peddler_effect(self.color_player.player)


class MarketPlayerBuilding(PlayerBuilding):
    """Market player building."""

    def __init__(self, belongs_to_beginner_version: bool, can_be_a_prestige_building: bool,
                 allows_to_place_a_worker: bool, front_color: str, name: str, n_prestige_pts: int,
                 primary_effect: Effect, resource_costs, can_be_a_residential_building: bool, secondary_effect: Effect,
                 color_player: ColorPlayer):
        """Initialization of a market player building."""
        PlayerBuilding.__init__(self, belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                                front_color, name, n_prestige_pts, primary_effect, resource_costs,
                                can_be_a_residential_building, secondary_effect, color_player)

    def apply_primary_effect(self, player: Player) -> None:
        """Apply the primary effect of a market player building."""
        """
        Exchange 1 cube from your personal stock with 4 deniers.
        """
        # Remark: Hard-coded! We don't use the tags <cost><CHOICES>... and <gain><n_deniers>+4... in <game_elements><buildings><player_buildings><player_building><primary_effect>.
        super().apply_primary_effect(player)
        money_resource_cost, qty_cost = None, -1  # type: Resource, int # None for any resource (including wild).
        money_resource_gain, qty_gain = Money.money, +4  # type: Money, int
        money_resource_cost_choices = [money_resource for money_resource, qty in player.current_money_resources.items()
                                       if money_resource != Money.money and qty + qty_cost >= 0
                                       ]  # type: List[Resource] # All suffisant available resources.
        if not money_resource_cost_choices:
            print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                  ' and can\'t apply the effect because he/she doesn\'t have resource as ' +
                  str(qty_cost) + ' required.')
        else:
            # The player do not have to use the effect; otherwie, the exchange is applied.
            money_resource_cost = player.choose_exchange_resource(True, qty_cost, money_resource_cost_choices,
                                                                  money_resource_gain, qty_gain)
            # We apply the exchange if the player wants to do it.
            if money_resource_cost is None:
                print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                      ' and didn\'t use the effect.')
            else:
                player.current_money_resources[money_resource_cost] += qty_cost
                player.current_money_resources[money_resource_gain] += qty_gain
                print(indent(4) +
                      player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) + '.')

    def apply_secondary_effect(self) -> None:
        """Apply the secondary effect of a market player building."""
        super().apply_secondary_effect()
        self.apply_no_cost_only_gain_effect(self.secondary_effect.money_resources_gain, self.color_player.player)


class GoldMinePlayerBuilding(PlayerBuilding):
    """Gold mine player building."""

    def __init__(self, belongs_to_beginner_version: bool, can_be_a_prestige_building: bool,
                 allows_to_place_a_worker: bool, front_color: str, name: str, n_prestige_pts: int,
                 primary_effect: Effect, resource_costs, can_be_a_residential_building: bool, secondary_effect: Effect,
                 color_player: ColorPlayer):
        """Initialization of a gold mine player building."""
        PlayerBuilding.__init__(self, belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                                front_color, name, n_prestige_pts, primary_effect, resource_costs,
                                can_be_a_residential_building, secondary_effect, color_player)

    def apply_primary_effect(self, player: Player) -> None:
        """Apply the primary effect of a gold mine player building."""
        super().apply_primary_effect(player)
        self.apply_no_cost_only_gain_effect(self.primary_effect.money_resources_gain, player)

    def apply_secondary_effect(self) -> None:
        """Apply the secondary effect of a gold mine player building."""
        """
        Exchange 1 cube from your personal stock with 1 gold cube from the stock.
        """
        # Remark: Hard-coded! We don't use the tags <cost><CHOICES>... and <gain><n_gold_cubes>+1... in <game_elements><buildings><player_buildings><player_building><secondary_effect>.
        super().apply_secondary_effect()
        money_resource_cost, qty_cost = None, -1  # type: Resource, int # None for any resource but we eliminate wild (to avoid the case to exchange 1 wild with 1 wild!).
        money_resource_gain, qty_gain = Resource.get_wild_resource(), +1  # type: Resource, int
        player = self.color_player.player  # type: Player
        money_resource_cost_choices = [money_resource for money_resource, qty in player.current_money_resources.items()
                                       if money_resource != Money.money and not money_resource.is_wild()
                                       and qty + qty_cost >= 0
                                       ]  # type: List[Resource] # All suffisant available resources excepted wild.
        if not money_resource_cost_choices:
            print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                  ' and can\'t apply the effect because he/she doesn\'t have resource (wild is not considered) as ' +
                  str(qty_cost) + ' required.')
        else:
            # The player can have or not the choice of the resource.
            if len(money_resource_cost_choices) == 1:
                money_resource_cost = money_resource_cost_choices[0]
                print(indent(4) +
                      player.name() + 'can only exchange resource ' + money_resource_cost.name + ', and it is done.')
            else:
                money_resource_cost = player.choose_exchange_resource(False, qty_cost, money_resource_cost_choices,
                                                                      money_resource_gain, qty_gain)
            # We apply the exchange.
            player.current_money_resources[money_resource_cost] += qty_cost
            player.current_money_resources[money_resource_gain] += qty_gain
            print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) + '.')


class BankPlayerBuilding(PlayerBuilding):
    """Bank player building."""

    def __init__(self, belongs_to_beginner_version: bool, can_be_a_prestige_building: bool,
                 allows_to_place_a_worker: bool, front_color: str, name: str, n_prestige_pts: int,
                 primary_effect: Effect, resource_costs, can_be_a_residential_building: bool, secondary_effect: Effect,
                 color_player: ColorPlayer):
        """Initialization of a bank player building."""
        PlayerBuilding.__init__(self, belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                                front_color, name, n_prestige_pts, primary_effect, resource_costs,
                                can_be_a_residential_building, secondary_effect, color_player)

    def apply_primary_effect(self, player: Player) -> None:
        """Apply the primary effect of a bank player building."""
        """
        Buy 1 gold from the stock with 1 denier or buy 2 gold from the stock with 3 deniers.
        """
        # Remark: Hard-coded! We don't use the tag <CHOICES>... in <game_elements><buildings><player_buildings><player_building><secondary_effect>.
        super().apply_primary_effect(player)
        all_costs = [(Money.money, -1), (Money.money, -3)]  # type: List[Tuple[Money, int]] # Ordered!
        resource_gain_choices, single_qty_gain = [Resource.get_wild_resource()], \
                                                 +1  # type: List[Resource], int # single_qty_gain must be equals to one!
        self.apply_effect_multi(player, all_costs, resource_gain_choices, single_qty_gain)

    def apply_secondary_effect(self) -> None:
        """Apply the secondary effect of a bank player building."""
        """
        Buy 1 gold from the stock with 2 deniers.
        """
        # Remark: Hard-coded! We don't use the tags <cost><n_deniers>-2 and <gain><n_gold_cubes>+1 in <game_elements><buildings><player_buildings><player_building><secondary_effect>.
        super().apply_secondary_effect()
        money_resource_cost, qty_cost = Money.money, -2  # type: Money, int
        player = self.color_player.player  # type: Player
        if player.current_money_resources[money_resource_cost] + \
                qty_cost < 0:  # Has the player enough money or resource?
            print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                  ' and can\'t apply the effect because he/she doesn\'t have enough money or resource as ' +
                  str(qty_cost) + ' ' + money_resource_cost.name + '(s) required.')
        else:
            resource_gain_choices, qty_gain = [Resource.get_wild_resource()], +1  # type: List[Resource], int
            resource_gain = player.choose_buy_resource(money_resource_cost, qty_cost, resource_gain_choices,
                                                       qty_gain)  # type: Resource
            if resource_gain is None:
                print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                      ' and had chosen to don\'t apply the effect.')
            else:
                print(indent(4) + player.name() + ' wants to consume ' +
                      str(qty_cost) + ' ' + money_resource_cost.name + '(s) to obtain ' +
                      str(qty_gain) + ' ' + resource_gain.name + '(s).')
                player.current_money_resources[money_resource_cost] += qty_cost
                player.current_money_resources[resource_gain] += qty_gain
                print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) +
                      ' once the effect applied.')


class ChurchPlayerBuilding(PlayerBuilding):
    """Church player building."""

    def __init__(self, belongs_to_beginner_version: bool, can_be_a_prestige_building: bool,
                 allows_to_place_a_worker: bool, front_color: str, name: str, n_prestige_pts: int,
                 primary_effect: Effect, resource_costs, can_be_a_residential_building: bool, secondary_effect: Effect,
                 color_player: ColorPlayer):
        """Initialization of a church player building."""
        PlayerBuilding.__init__(self, belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                                front_color, name, n_prestige_pts, primary_effect, resource_costs,
                                can_be_a_residential_building, secondary_effect, color_player)

    def apply_primary_effect(self, player: Player) -> None:
        """Apply the primary effect of a church player building."""
        """
        Buy 1 Castle token with 2 deniers, or buy 2 Castle tokens with 5 deniers.
        """
        # Remark: Hard-coded! We don't use the tag <CHOICES>... in <game_elements><buildings><player_buildings><player_building><secondary_effect>.
        super().apply_primary_effect(player)
        self.apply_effect_buy_castle_multi(player, [(Money.money, -2), (Money.money, -5)])

    def apply_secondary_effect(self) -> None:
        """Apply the secondary effect of a church player building."""
        """
        Buy 1 Castle token with 3 deniers.
        """
        # Remark: Hard-coded! We don't use the tags <cost><n_deniers>-3 and <gain><n_castle_tokens>+1 in <game_elements><buildings><player_buildings><player_building><secondary_effect>.
        super().apply_secondary_effect()
        self.apply_effect_buy_castle_multi(self.color_player.player, [(Money.money, -3)])

    def apply_effect_buy_castle_multi(self, player: Player, all_costs) -> None:
        """Apply the primary or secondary effect of a church player building that is buy Castle tokens with deniers."""
        remaining_n_castle_tokens = Building.game_element.game.get_remaining_n_castle_tokens()  # type: int
        if remaining_n_castle_tokens == 0:
            print(indent(4) + 'The effect can\'t be applied because there are not tokens anymore in the castle.')
        else:
            # Display the tokens in the castle.
            print(indent(4) + 'The tokens in the castle are: ' +
                  TXT_SEPARATOR.join(str(castle.current_n_castle_tokens) + ' of ' + str(castle.n_prestige_pts) +
                                     ' prestige point(s) (' + castle.name + ')'
                                     for castle in Building.game_element.castle if castle.current_n_castle_tokens > 0) +
                  '.')
            # Prepare costs and gains.
            castle_gain_choices = [castle for castle in Building.game_element.castle
                                   for _counter in range(castle.current_n_castle_tokens)]  # type: List[Castle]
            single_qty_gain = +1  # type: int # Unused. # Must be equals to one!
            costs = [(money_resource_cost, qty_cost) for (money_resource_cost, qty_cost) in all_costs
                     if player.current_money_resources[money_resource_cost] + qty_cost >= 0]
            n_choices = min(len(costs), len(castle_gain_choices))  # type: int
            costs = costs[:n_choices]
            castle_gain_choices = castle_gain_choices[:n_choices]
            # Has the player enough money or resource?
            if n_choices == 0:
                print(indent(4) + player.txt_name_money_resources_workers_PPs_deck(True, False, False, True, False) +
                      ' and can\'t apply the effect because he/she doesn\'t have enough money or resource as ' +
                      'either ' + ' or '.join(str(qty_cost) + ' ' + money_resource_cost.name + '(s)'
                                              for (money_resource_cost, qty_cost) in all_costs) + ' required.')
            else:
                castles_gain = player.choose_buy_castle_multi(costs, castle_gain_choices)
                if not castles_gain:
                    print(indent(4) +
                          player.txt_name_money_resources_workers_PPs_deck(True, False, False, True, False) +
                          ' and had chosen to don\'t apply the effect.')
                else:
                    n_castles_gain = len(castles_gain)  # type: int
                    money_resource_cost, qty_cost = costs[
                        n_castles_gain - 1]  # type: List[MoneyResource], int # costs must be ordered!
                    print(indent(4) + player.name() + ' wants to consume ' +
                          str(qty_cost) + ' ' + money_resource_cost.name + '(s).')
                    player.current_money_resources[money_resource_cost] += qty_cost
                    for castle_gain, qty_gain in collections.Counter(castles_gain).items():  # To group by castle part.
                        print(indent(4) + player.name() + ' wants to obtain ' +
                              str(qty_gain) + ' ' + castle_gain.name + '(s) each giving ' +
                              str(castle_gain.n_prestige_pts) + ' prestige point(s).')
                        player.current_n_prestige_pts += castle_gain.n_prestige_pts * qty_gain
                        castle_gain.current_n_castle_tokens -= qty_gain
                    print(indent(4) +
                          player.txt_name_money_resources_workers_PPs_deck(True, False, False, True, False) +
                          ' once the effect applied.')
