#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Thu Sep. 4 18:29:00 2018
All elements required to play to the game Caylus Magna Carta.
@author: Olivier
"""

# Remark: in order to simplify this code, attributes (e.g. Castle.n_castle_tokens,
# SmallProductionPlayerBuilding.n_cubes_into_area, GameElement.n_all_except_last_neutral_buildings) depending on
# the number of players in the game are created as [None .. None, value(n_min_players) .. value(n_max_players)]
# and so are indexed by player numbers in the game.


import abc
import collections
import itertools
import random
import sys
import xml.etree.ElementTree as ET
from enum import Enum, unique
from os import path

TXT_SEPARATOR = ', '  # type: str # Separator between two elements of an enumeration of string elements.


def ordinal_number(n: int) -> str:
    """Get the ordinal number."""
    if n <= 0:
        raise Exception('The ordinal number is not defined for non-positive integers.')
    else:
        digit = n % 10  # type: int
        letter_suffix = None  # type: str
        if digit == 1:
            letter_suffix = 'st'
        elif digit == 2:
            letter_suffix = 'nd'
        elif digit == 3:
            letter_suffix = 'rd'
        else:
            letter_suffix = 'th'
        return str(n) + letter_suffix


def indent(n_indent: int) -> str:
    """Get a string in order to create an indentation."""
    return '  ' * n_indent


@unique
class Location(Enum):
    """Enumeration of all the possible locations of the player buildings."""
    HAND = 0
    PILE = 1
    DISCARD = 2
    ROAD = 3
    REPLACED = 4


class Version:
    """All 2 versions of the game: beginner and standard."""

    def __init__(self, name: str):
        """Initialization of a version of the game."""
        # Attributes obtained from the XML file.
        self.name = name  # type: str

    def is_beginner(self) -> bool:
        """Indicates if it is the beginner version; it is the standard version otherwise."""
        return self.name.lower() == 'beginner'


class ColorPlayer:
    """All 4 colors of the players: red, green, orange and blue."""

    colors_players = {}  # type: Dict[str, ColorPlayer] # All colors of players (indexed by their names).

    def __init__(self, name: str, background_player_building=None):
        """Initialization of a color of a player."""
        # Attributes obtained from the XML file.
        self.name = name  # type: str
        self.background_player_building = background_player_building  # type: BackgroundPlayerBuilding
        ColorPlayer.colors_players[name] = self
        # Attributes to play a game.
        self.player = None  # type: Player

    def setup(self, background_player_building) -> None:
        """Setup the background of a player building."""
        self.background_player_building = background_player_building


class Castle:
    """Castle is composed of 3 parts: dungeon, walls, towers."""
    """
    Prestige point tokens (for the 3 parts of the Castle) are sorted out according to their value and placed next to
    the Castle. In three player games, 1 token of each value is removed; in two player games, 2 tokens of each value are
    removed.
    """

    def __init__(self, front_color: str, name: str, n_castle_tokens, n_prestige_pts: int):
        """Initialization of a part (dungeon, walls, towers) of the castle."""
        # Attributes obtained from the XML file.
        self.front_color = front_color  # type: str
        self.name = name  # type: str
        self.n_castle_tokens = n_castle_tokens  # type: Array[int]
        self.n_prestige_pts = n_prestige_pts  # type: int
        # Attributes to play a game.
        self.current_n_castle_tokens = None  # type: int

    def setup(self, n_players: int) -> None:
        """Setup the part (dungeon, walls, towers) of the castle."""
        self.current_n_castle_tokens = self.n_castle_tokens[n_players]  # type: int


class MoneyResource:
    """Money or Resource."""

    def __init__(self, name: str, number: int):
        """Initialization of money or resource."""
        # Attributes obtained from the XML file.
        self.name = name  # type: str
        self.number = number  # type: int
        # Attributes to play a game.
        self.current_number = self.number  # type: int # Unused because money and resources can be considered infinite.

    def get_name_abbreviation(self) -> str:
        """Get the abbreviation of money or resource name."""
        return self.name[0].upper()


class Money(MoneyResource):
    """Money (coins)."""

    money = None  # type: Money

    def __init__(self, name: str, number: int):
        """Initialization of the money."""
        MoneyResource.__init__(self, name, number)
        Money.money = self


class Resource(MoneyResource):
    """4 types of resources (cubes): food, wood, stone or gold."""
    """
    Gold is a wild resource: a cube of gold equals a cube of any type.
    """

    resources = {}  # type: Dict[str, Resource] # All resources where the key is the resource name and the value is the resource.

    def __init__(self, name: str, number: int):
        """Initialization of a resource."""
        MoneyResource.__init__(self, name, number)
        # self.is_wild = is_wild  # Unused because it is not present into the XML file. # Warning: it is commented in order to avoid a conflict with is_wild().
        Resource.resources[name] = self

    @staticmethod
    def get_resource(name: str):  # -> Resource
        """Get a resource from its name."""
        return Resource.resources.get(name)

    @staticmethod
    def get_name_abbreviation_resources(resources=None):  # -> Dict[str[1], Resource] # E.g. {'F': food, ...}.
        """Get the resource name abbreviations and the resources."""
        if resources is None:
            return {resource.get_name_abbreviation(): resource for resource in Resource.resources.values()}
        else:
            return {resource.get_name_abbreviation(): resource for resource in resources}

    def is_wild(self) -> bool:
        """Is it a wild resource?"""
        """
        Remark: this method exists only because such information lacks in the XML file. 
        """
        return self.name.lower() == 'gold'

    @staticmethod
    def get_wild_resource():  # -> Resource:
        """Get the (unique) wild resource."""
        return [resource for resource in Resource.resources.values() if resource.is_wild()][0]


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


class Player():
    """Player."""
    """
    Each player chooses a color and takes the corresponding cards and pawns.
    """

    txt_separator_name = '='  # type: str
    n_workers = None  # type: int
    money_resources = None  # type: Dict[MoneyResource, int]
    n_prestige_pts = None  # type: int # Number of prestige points obtained from tokens of the castle and prestige buildings for a beginner version.

    def __init__(self, color_player: ColorPlayer):
        """Initialization of a player."""
        # Attributes obtained from the XML file.
        self.color_player = color_player  # type: ColorPlayer
        # Attributes to play a game.
        self.current_n_workers = None  # type: int
        self.current_money_resources = None  # type: Dict[MoneyResource, int]
        self.current_n_prestige_pts = None  # type: int
        self.deck = None  # type: Dict[PlayerBuilding, Location]

    def name(self) -> str:
        """Get the default name of the player."""
        return '"' + self.color_player.name + '"'

    @abc.abstractmethod
    def is_human(self) -> bool:
        """Indicates whether the player is a human or an artificial intelligence."""
        pass

    def setup(self) -> None:
        """Setup the player."""
        self.color_player.player = self
        self.current_n_workers = Player.n_workers
        self.current_money_resources = Player.money_resources.copy()
        self.current_n_prestige_pts = Player.n_prestige_pts

    def get_residence_building(self):  # -> BackgroundPlayerBuilding:
        return self.color_player.background_player_building

    def get_player_buildings_by_location(self, location_expected: Location = None):  # -> List[BuildingPlayer]
        """Get the player buildings of his/her deck in an expected location."""
        if location_expected is None:
            return list(self.deck.keys())
        else:
            return [player_building for player_building, location in self.deck.items() if location == location_expected]

    def move_all_buildings_from_to_location(self, location_source: Location, location_destination: Location) -> None:
        """Move all buildings from a source location (e.g. pile, hand, discard) to a destination location (e.g. pile, hand, discard)."""
        for player_building in self.get_player_buildings_by_location(location_source):
            self.deck[player_building] = location_destination

    def txt_name_money_resources_workers_PPs_deck(self, with_money: bool, with_resources: bool, with_workers: bool,
                                                  with_prestige_points: bool,
                                                  with_n_buildings_by_location: bool) -> str:
        """Get the text of the player name with the money and resources (always in the same order, wild last), workers, prestige points and number of buildings by location."""
        # Warning: we don't use (m_r, qty) in self.current_money_resources.items() in order to always have the same order for resources.
        get_name_money_resources_workers_PPs_deck = list()  # type: list[str]
        if with_money:
            get_name_money_resources_workers_PPs_deck.append(str(self.current_money_resources[Money.money]) + ' ' +
                                                             Money.money.name + '(s)')
        if with_resources:
            get_name_money_resources_workers_PPs_deck.append('resources = (' + TXT_SEPARATOR.join(
                [str(self.current_money_resources[resource]) + ' ' + resource.name + '(s)'
                 for resource in Resource.resources.values() if not resource.is_wild()] +
                [str(self.current_money_resources[Resource.get_wild_resource()]) + ' ' +
                 Resource.get_wild_resource().name + '(s)']) + ')')
        if with_workers:
            get_name_money_resources_workers_PPs_deck.append(str(self.current_n_workers) + ' worker(s)')
        if with_prestige_points:
            get_name_money_resources_workers_PPs_deck.append(str(self.current_n_prestige_pts) +
                                                             ' prestige point(s)')
        if with_n_buildings_by_location:
            get_name_money_resources_workers_PPs_deck.append('buildings = (' + TXT_SEPARATOR.join([
                str(n_buildings) + ' in ' + location.name.lower()
                for location, n_buildings in collections.Counter(self.deck.values()).items()
                if n_buildings > 0]) + ')')
        return self.name() + ' has got: ' + TXT_SEPARATOR.join(get_name_money_resources_workers_PPs_deck)

    def resource_all_payments(self, resource_costs):  # -> List[Dict[Resource, int]]
        """Get all possible payments of resources according to the cost of resources (including any cube resources).
        Remark: wild resource is used for missing resources if and only if it is necessary."""
        # E.g.: current_money_resources = 3F,2W,3S,3G and resource_costs = -1F,-3W,(S),-1G requires resource_payments = -1F,-2W,-0S,-1G-1G.
        # E.g.: current_money_resources = 3F,2W,3S,3G and resource_costs = -1any,(F),-1W,(S),(G) requires resource_payments = -1F,-1W,-0S,-0G or -0F,-2W,-0S,-0G or -0F,-1W,-1S,-0G (but not -0F,-1W,-0S,-1G).
        resource_all_payments = list()  # type: List[Dict[Resource, int]]
        if None in resource_costs.keys():
            # We have to consider the case of any cube resources.
            resources_not_wild = [resource for resource in Resource.resources.values()
                                  if not resource.is_wild()]  # type: List[Resource]
            for resources_not_wild_to_use in itertools.combinations_with_replacement(resources_not_wild,
                                                                                     -resource_costs[None]):
                resource_costs_to_use = {}  # type: Dict[Resource]
                for resource in Resource.resources.values():  # All resources, including wild.
                    resource_costs_to_use[resource] = 0
                for resource, qty_cost in resource_costs.items():  # All costs of resources, including eventually wild.
                    if resource is not None:  # Any cube resources will be replaced by (non wild) resources.
                        resource_costs_to_use[resource] = qty_cost
                for resource_not_wild_to_use in resources_not_wild_to_use:
                    # 1 cube resource is replaced by 1 (non wild) resource.
                    resource_costs_to_use[resource_not_wild_to_use] -= 1
                resource_payments = self.resource_payments(resource_costs_to_use)  # type: Dict[Resource, int]
                if resource_payments is not None and not any([resource_payments == resource_1_payments
                                                              for resource_1_payments in resource_all_payments]):
                    resource_all_payments.append(resource_payments)  # One more payment of resources.
                else:
                    pass  # The player can't pay the cost or we have already found this resource_payments.
        else:
            # We don't have to consider the case of any cube resources.
            resource_payments = self.resource_payments(resource_costs)  # type: Dict[Resource, int]
            if resource_payments is not None:
                resource_all_payments.append(resource_payments)  # Return only one payment of resources.
            else:
                pass  # Return list() because the player can't pay the cost.
        return resource_all_payments

    def resource_payments(self, resource_costs):  # Optional[Dict[Resource, int]]
        """Get one payment of resources for the cost of resources without the case of any cube resources.
        Remark: wild resource is used for missing resources if and only if it is necessary."""
        resource_payments = {}  # type: Dict[Resource, int]
        wild_resource = Resource.get_wild_resource()  # type: Resource
        for resource in Resource.resources.values():  # All resources, including wild.
            resource_payments[resource] = 0
        for resource, qty_cost in resource_costs.items():  # All costs of resources, including eventually wild.
            resource_payments[resource] = -min(self.current_money_resources[resource], -qty_cost)
        n_necessary_wild_resources = sum([qty_cost - resource_payments[resource]
                                          for resource, qty_cost in resource_costs.items()])  # type: int
        resource_payments[wild_resource] += n_necessary_wild_resources  # Add necessary wild resources.
        return None if self.current_money_resources[wild_resource] + resource_payments[wild_resource] < 0 else \
            resource_payments

    def n_max_batches_to_castle(self, castle_phase: CastlePhase) -> int:
        """Get the maximum number of batches to offer to the castle."""
        # We must have the costs of the castle resources s.t. they never require a wild resource.
        resources_not_wild = {resource_not_wild: self.current_money_resources.get(resource_not_wild)
                              for resource_not_wild in Resource.resources.values()
                              if not resource_not_wild is None and not resource_not_wild.is_wild()
                              }  # type: Dict[Resource, int]
        n_wild = self.current_money_resources.get(Resource.get_wild_resource())  # type: int
        # We first initialize the maximum number of batches for the castle without wild resource.
        n_max_batches_to_castle = min([int(resources_not_wild.get(resource_cost) / -qty)
                                       for resource_cost, qty in castle_phase.resource_costs.items()])  # type: int
        for resource_cost, qty in castle_phase.resource_costs.items():
            resources_not_wild[resource_cost] += qty * n_max_batches_to_castle  # First batches.
        # We now use wild resources.
        n_necessary_wild_resources = -sum([min(0, resources_not_wild[resource_cost] + qty)
                                           for resource_cost, qty in castle_phase.resource_costs.items()])  # type: int
        while n_wild >= n_necessary_wild_resources:
            # One new batch.
            for resource_cost, qty in castle_phase.resource_costs.items():
                resources_not_wild[resource_cost] = max(0, resources_not_wild[resource_cost] + qty)
            n_max_batches_to_castle += 1
            n_wild -= n_necessary_wild_resources
            n_necessary_wild_resources = -sum([min(0, resources_not_wild[resource_cost] + qty)
                                               for resource_cost, qty in castle_phase.resource_costs.items()])
        return n_max_batches_to_castle

    def consume_n_max_batches_to_castle(self, n_max_batches_to_castle: int, castle_phase: CastlePhase) -> int:
        """Consume some number of batches to offer to the castle."""
        # We assume it is possible.
        n_necessary_wild_resources = 0  # type: int
        for resource_cost, qty in castle_phase.resource_costs.items():
            qty_remaining = self.current_money_resources.get(resource_cost) + qty * n_max_batches_to_castle  # type: int
            if qty_remaining >= 0:
                self.current_money_resources[resource_cost] = qty_remaining
            else:
                self.current_money_resources[resource_cost] = 0
                n_necessary_wild_resources -= qty_remaining
        self.current_money_resources[Resource.get_wild_resource()] -= n_necessary_wild_resources

    def tot_n_prestige_pts(self, buildings_road) -> int:
        """Get the total number of prestige points of the player."""
        """
        Each player adds up their prestige points as follows:
        ● each token in their possession is worth its value in prestige points (4, 3 or 2 PPs)
        ● [Beginner version] the buildings the player has built along the road yield prestige points, as shown in the top right-hand corner of the card (buildings which remain in the player’s hand yield no points).
        ● [Beginner version] the prestige buildings the player has built yield prestige points as shown in the top right-hand corner of the card.
        ● [Standard version] the buildings the player has built along the road yield points according to their visible value only: thus, if a building has been transformed into a residential building, it only yields 1 point. A residential building yields no point if a prestige building has been built on top of it; the prestige building yields its points normally.
        ● each gold cube yields 1 PP
        ● each group of any 3 cubes (except gold) yields 1 PP
        ● each group of 3 deniers yields 1 PP
        """
        # Remark: for the beginner version, prestige points of prestige buildings are already added to self.current_n_prestige_pts (and these buildings are not along the road). So, we just have to add the prestige points of all the buildings along the road (player buildings for both versions on one hand and background player buildings and prestige buildings for the standard version in the other hand).
        return self.current_n_prestige_pts + \
               sum(building.n_prestige_pts for building in buildings_road) + \
               sum([self.current_money_resources.get(resource_wild)
                    for resource_wild in Resource.resources.values()
                    if not resource_wild is None and resource_wild.is_wild()]) + \
               int(sum([self.current_money_resources.get(resource_not_wild)
                        for resource_not_wild in Resource.resources.values()
                        if not resource_not_wild is None and not resource_not_wild.is_wild()]) / 3) + \
               int(self.current_money_resources.get(Money.money) / 3)

    @abc.abstractmethod
    def choose_discard_hand_for_new(self) -> bool:
        """Each player can discard all the cards in his/her hand and take new cards."""
        pass

    @abc.abstractmethod
    def choose_action(self, possible_actions):
        """Choose one of the possible actions."""
        pass

    @abc.abstractmethod
    def choose_n_provost_movement(self, n_min_provost_movements_player: int,
                                  n_max_provost_movements_player: int) -> int:
        """Each player can move the Provost along the road by paying deniers."""
        pass

    @abc.abstractmethod
    def choose_buy_resource(self, money_resource_cost: MoneyResource, qty_cost: int, resource_gain_choices,
                            qty_gain: int) -> Resource:
        """A player can choose to buy some resource with money (e.g. peddler neutral building, secondary effects of peddler and bank player buldings)."""
        pass

    @abc.abstractmethod
    def choose_buy_resource_multi(self, costs, resource_gain_choices, qty_gain: int):  # -> List[Resource]
        """A player can choose to apply 0, 1 or 2 times to buy some resource with money (e.g. primary effects of peddler and bank player buldings)."""
        # :param costs: # type: List[(MoneyResource, int)]
        pass

    @abc.abstractmethod
    def choose_buy_castle_multi(self, costs, castle_gain_choices):  # -> List[Castle]
        """A player can choose to apply several (one or more) times to buy some tokens of the castle with money (e.g. effects of church player buldings)."""
        # :param costs: # type: List[(MoneyResource, int)]
        pass

    @abc.abstractmethod
    def choose_exchange_resource(self, can_no_use_effect: bool, qty_cost: int, resource_cost_choices,
                                 money_resource_gain: MoneyResource, qty_gain: int) -> Resource:
        """A player can choose to exchange some resource with some money or other resource, and may not use the effect (e.g. primary effect of market player building, secondary effect of gold mine player building)."""
        pass

    @abc.abstractmethod
    def choose_construct_residence(self, resource_costs, i_road_buildings_on_road):  # -> Optional[Tuple[int, Building]]
        """Each player can construct a residential building by turning over one of his/her cards along the road."""
        pass

    @abc.abstractmethod
    def choose_n_batches_to_castle(self, n_max_batches_to_castle: int) -> int:
        """Each player may offer batches to the castle."""
        pass


class HumanPlayer(Player):
    """Human player."""

    def __init__(self, color_player: ColorPlayer):
        """Initialization of an AI player."""
        Player.__init__(self, color_player)

    def is_human(self) -> bool:
        """Indicates that it is an human player."""
        return True

    def name(self) -> str:
        """Get the name of the human player."""
        return '"' + self.color_player.name + Player.txt_separator_name + 'you!"'

    def print_buildings_by_location(self, n_indent: int) -> None:
        """Display the player buildings of the player that is the location of the buildings in the deck: in the pile, the hand and the discard (but neither along the road nor replaced) ."""
        print(indent(n_indent) + self.name() + ', location of your buildings: ')
        for location in Location:
            player_building_names_by_location = sorted([player_building.name
                                                        for player_building in
                                                        self.get_player_buildings_by_location(location)]
                                                       )  # type: List[PlayerBuilding]
            if player_building_names_by_location:
                print(indent(n_indent + 1) + location.name.lower() + ': ' +
                      TXT_SEPARATOR.join(player_building_names_by_location) + '.')

    def choose_discard_hand_for_new(self) -> bool:
        self.print_buildings_by_location(0)
        response = input('Do you want to discard all the cards in your hand and to take new cards? [Y/N] ')  # type: str
        return self.check_response_yes_no(response, 1)

    def choose_action(self, possible_actions):
        self.print_buildings_by_location(3)
        n_possible_actions = len(possible_actions)  # type: int # >= 1 because it must contain the passing action.
        if n_possible_actions == 1:
            print(indent(3) + 'You don\'t have any choice and you have to do the action: ' + possible_actions[0][1])
            return possible_actions[0]
        else:
            print(indent(3) + 'Here are all the possible action(s):')
            for i_possible_actions, possible_action in enumerate(possible_actions):
                print(indent(4) + str(i_possible_actions) + ': ' + possible_action[1])
            response = input(indent(3) +
                             'Which action do you choose? [0..' + str(n_possible_actions - 1) + '] ')  # type: str
            return possible_actions[self.check_response_in_interval(response, 0, n_possible_actions - 1, 4)]

    def choose_n_provost_movement(self, n_min_provost_movements_player: int,
                                  n_max_provost_movements_player: int) -> int:
        response = input(indent(3) + 'How long do you want to move the Provost? [' +
                         str(n_min_provost_movements_player) + '..' + str(n_max_provost_movements_player) +
                         '] ')  # type: str
        return self.check_response_in_interval(response, n_min_provost_movements_player, n_max_provost_movements_player,
                                               4)

    def choose_buy_resource(self, money_resource_cost: MoneyResource, qty_cost: int, resource_gain_choices,
                            qty_gain: int) -> Resource:
        possibilities = list(Building.ABBREV_NO_USE_EFFECT)  # type: List[str[1]]
        abbrev_resource_name_resource = {}  # type: Dict[str[1], Resource] # E.g. {'F': food, ...}.
        for resource in resource_gain_choices:
            abbrev_resource_name = resource.get_name_abbreviation()
            abbrev_resource_name_resource[abbrev_resource_name] = resource
            possibilities.append(abbrev_resource_name)
        print(indent(4) + self.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) + '.')
        response = input(indent(4) + 'Do you want to consume ' + str(qty_cost) + ' ' + money_resource_cost.name +
                         '(s) to obtain ' + str(qty_gain) + ' resource ' + Building.TXT_NO_USE_EFFECT +
                         '? [' + '/'.join(possibilities) + '] ')  # type: str
        response = self.check_response_in_possibilities(response, possibilities, 5)
        return None if response == Building.ABBREV_NO_USE_EFFECT else abbrev_resource_name_resource[response]

    def choose_buy_resource_multi(self, costs, resource_gain_choices, qty_gain: int):  # -> List[Resource]
        # Remark: we only consider the case that costs is a List[Tuple[Money,int]] without resource and of length 2 or more.
        possibilities = list(Building.ABBREV_NO_USE_EFFECT)  # type: List[str[1..qty_gain]]
        abbrev_resource_name_resource = {resource.get_name_abbreviation(): resource
                                         for resource in resource_gain_choices
                                         }  # type: Dict[str[1], Resource] # E.g. {'F': food, ...}.
        possibilities.extend([''.join(
            resource_gain.get_name_abbreviation() for resource_gain in list(resource_gain_choice))
            for n_parts in range(1, qty_gain + 1)
            for resource_gain_choice in itertools.combinations_with_replacement(resource_gain_choices, n_parts)])
        print(indent(4) + self.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) + '.')
        response = input(indent(4) + 'Do you want to consume either ' +
                         ' or '.join(str(qty_cost) + ' ' + money_resource_cost.name +
                                     '(s) for ' + str(1 + i_costs) + ' resource(s)'
                                     for i_costs, (money_resource_cost, qty_cost) in enumerate(costs)) +
                         ' ' + Building.TXT_NO_USE_EFFECT + '? [' + '/'.join(possibilities) + '] ')  # type: str
        response = self.check_response_in_possibilities(response, possibilities, 5)
        choose_buy_resource_multi = list()
        if response != Building.ABBREV_NO_USE_EFFECT:
            for abbrev_resource_name in response:
                choose_buy_resource_multi.append(abbrev_resource_name_resource[abbrev_resource_name])
        return choose_buy_resource_multi

    def choose_buy_castle_multi(self, costs, castle_gain_choices):  # -> List[Castle]
        n_min_castle_gain = 0  # type: int
        n_max_castle_gain = len(castle_gain_choices)  # type: int
        response = input(indent(4) + 'How many tokens of parts of the castle among [' +
                         ', '.join(castle.name for castle in castle_gain_choices) + '] do you want to buy with: ' +
                         ' or '.join(str(qty_cost) + ' ' + money_resource_cost.name + '(s)'
                                     for (money_resource_cost, qty_cost) in costs) +
                         '? [' + str(n_min_castle_gain) + '..' + str(n_max_castle_gain) + '] ')  # type: str
        return castle_gain_choices[:self.check_response_in_interval(response, n_min_castle_gain, n_max_castle_gain, 5)]

    def choose_exchange_resource(self, can_no_use_effect: bool, qty_cost: int, resource_cost_choices,
                                 money_resource_gain: MoneyResource, qty_gain: int) -> Resource:
        abbrev_resource_name_resources = Resource.get_name_abbreviation_resources(resource_cost_choices)
        possibilities = list()  # type: List[str[1]]
        if can_no_use_effect:
            possibilities.append(Building.ABBREV_NO_USE_EFFECT)
        possibilities += list(abbrev_resource_name_resources.keys())
        print(indent(4) + self.txt_name_money_resources_workers_PPs_deck(True, True, False, False, False) + '.')
        response = input(indent(4) + 'Do you want to exchange '
                         + str(qty_cost) + ' of some resource with ' + str(qty_gain) + ' ' + money_resource_gain.name +
                         (' or not use the effect ' + Building.TXT_NO_USE_EFFECT if can_no_use_effect else '') +
                         '? [' + '/'.join(possibilities) + '] ')  # type: str
        response = self.check_response_in_possibilities(response, possibilities, 5)
        return None if response == Building.ABBREV_NO_USE_EFFECT else abbrev_resource_name_resources[response]

    def choose_construct_residence(self, resource_costs, i_road_buildings_on_road):  # -> Optional[Tuple[int, Building]]
        n_min_i_building = 0  # type: int
        n_max_i_building = len(i_road_buildings_on_road)  # type: int
        response = input(indent(4) + 'Which of your ' + str(n_max_i_building) + ' building(s) [' +
                         ', '.join(building_on_road.name for (i_road, building_on_road) in i_road_buildings_on_road) +
                         '] do you want to choose (or ' + str(n_min_i_building) +
                         ' if you don\'t want to use the effect)? [' + str(n_min_i_building) + '..' +
                         str(n_max_i_building) + '] ')  # type: str
        response = self.check_response_in_interval(response, n_min_i_building, n_max_i_building, 5)  # type: int
        return None if response == n_min_i_building else i_road_buildings_on_road[response - 1]

    def choose_n_batches_to_castle(self, n_max_batches_to_castle: int) -> int:
        response = input(indent(3) + 'How many batches do you want to offer to the castle? [0..' +
                         str(n_max_batches_to_castle) + '] ')  # type: str
        return self.check_response_in_interval(response, 0, n_max_batches_to_castle, 4)

    def check_response_yes_no(self, response: str, n_indent: int) -> bool:
        """Check that a (string) response is (a boolean) yes or no."""
        return self.check_response_in_possibilities(response, ['Y', 'N'], n_indent) == 'Y'

    def check_response_in_possibilities(self, response: str, possibilities, n_indent: int) -> str:
        """Check that a (string) response is in a list of (str[1..2]) possibilities."""
        while len(response) == 0 or response.upper() not in possibilities:
            response = input(indent(n_indent) + 'Please: ')
        return response.upper()

    def check_response_in_interval(self, response: str, n_min: int, n_max: int, n_indent: int) -> int:
        """Check that a (string) response is in an interval (of numeric values)."""
        is_response_ok = False  # type: bool
        while not is_response_ok:
            try:
                response_ok = int(response)  # type: int
                is_response_ok = n_min <= response_ok <= n_max  # Is in the interval?
            except ValueError:
                is_response_ok = False  # Not a numeric.
            if not is_response_ok:
                response = input(indent(n_indent) + 'Please: ')
        return response_ok


class AIPlayer(Player):
    """AI (artificial intelligence) player."""

    def __init__(self, color_player: ColorPlayer):
        """Initialization of an AI player."""
        Player.__init__(self, color_player)

    @staticmethod
    def ai_names():  # -> List[str]
        """AI (artificial intelligence) names."""
        return [BasicAIPlayer.ai_name, AdvancedAIPlayer.ai_name]

    def is_human(self) -> bool:
        """Indicates that AI player is not an human player."""
        return False

    def choose_discard_hand_for_new(self) -> bool:
        return bool(random.getrandbits(1))  # proba(True) = proba(False) = 0.5

    def choose_action(self, possible_actions):
        return possible_actions[random.randrange(len(possible_actions))]

    def choose_n_provost_movement(self, n_min_provost_movements_player: int,
                                  n_max_provost_movements_player: int) -> int:
        return random.randint(n_min_provost_movements_player,
                              n_max_provost_movements_player)  # n_min_provost_movements_player..n_max_provost_movements_player

    def choose_buy_resource(self, money_resource_cost: MoneyResource, qty_cost: int, resource_gain_choices,
                            qty_gain: int) -> Resource:
        n_choice = random.randrange(len(resource_gain_choices) + 1)  # type: int
        return None if n_choice == len(resource_gain_choices) else resource_gain_choices[n_choice]

    def choose_buy_resource_multi(self, costs, resource_gain_choices, qty_gain: int):  # -> List[Resource]
        choices = [list(choice) for n_parts in range(qty_gain + 1)
                   for choice in itertools.combinations_with_replacement(resource_gain_choices, n_parts)]
        return choices[random.randrange(len(choices))]

    def choose_buy_castle_multi(self, costs, castle_gain_choices):  # -> List[Castle]
        return castle_gain_choices[:random.randrange(len(castle_gain_choices) + 1)]

    def choose_exchange_resource(self, can_no_use_effect: bool, qty_cost: int, resource_cost_choices,
                                 money_resource_gain: MoneyResource, qty_gain: int) -> Resource:
        n_choice = random.randrange(len(resource_cost_choices) + (1 if can_no_use_effect else 0))  # type: int
        return None if n_choice == len(resource_cost_choices) else resource_cost_choices[n_choice]

    def choose_construct_residence(self, resource_costs, i_road_buildings_on_road):  # -> Optional[Tuple[int, Building]]
        n_choice = random.randrange(len(i_road_buildings_on_road) + 1)  # type: int
        return None if n_choice == len(i_road_buildings_on_road) else i_road_buildings_on_road[n_choice]

    def choose_n_batches_to_castle(self, n_max_batches_to_castle: int) -> int:
        return random.randrange(n_max_batches_to_castle + 1)  # 0..n_max_batches_to_castle


class BasicAIPlayer(AIPlayer):
    """Basic AI (artificial intelligence) player."""

    ai_name = 'Basic'  # type: str

    def __init__(self, color_player: ColorPlayer):
        """Initialization of a basic AI player."""
        AIPlayer.__init__(self, color_player)

    def name(self) -> str:
        """Get the name of a basic AI player."""
        return '"' + self.color_player.name + Player.txt_separator_name + BasicAIPlayer.ai_name + '"'


class AdvancedAIPlayer(AIPlayer):
    """Advanced AI (artificial intelligence) player."""

    ai_name = 'Advanced'  # type: str

    def __init__(self, color_player: ColorPlayer):
        """Initialization of an advanced AI player."""
        AIPlayer.__init__(self, color_player)

    def name(self) -> str:
        """Get the name of an advanced AI player."""
        return '"' + self.color_player.name + Player.txt_separator_name + AdvancedAIPlayer.ai_name + '"'


class Effect:
    """Effect (primary or secondary) of a building."""

    def __init__(self, text: str, phase: Phase, money_resources_cost=None, money_resources_gain=None):
        """Initialization of an effect of a building."""
        self.text = text  # type: str
        self.phase = phase  # type: Phase
        self.money_resources_cost = money_resources_cost  # unused
        self.money_resources_gain = money_resources_gain  # type: Tuple[MoneyResource, int]


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


class Game:
    """Game Caylus Magna Carta."""

    def __init__(self, game_element, version, players):
        """Initialization of the game."""
        # Attributes obtained from the XML file.
        self.game_element = game_element  # type: GameElement
        self.version = version  # type: Version
        self.players = players  # type: List[Player]
        # Attributes to play a game.
        self.n_players = None  # type: int
        self.current_buildings = None  # type: List[Building]  # Buildings used for the game.
        self.road = None  # type: List[List[Building, Optional[Player], Optional[Building]]] # Remark: Tuple becomes List because it does not support item assignment. # Buildings and workers on the road. # Remark. : the optional building corresponds to the case there is a worker on a player building which becomes a résidence player buiding (and perhaps a prestige building during the same round or later); in such case, the primary and secondary effects have to be applied on the player building.
        self.i_provost = None  # type: int # Index of the Provost in the road; None (instead of -1) for the standard version.
        self.passing_marker_players = None  # type: List[Player]
        self.i_first_player = None  # type: int # Index of the first player among the players.

    def setup(self) -> None:
        """Setup of the game."""
        # Setup the number of players.
        self.n_players = len(self.players)
        # Reinitialize the color of the player for all the prestige buildings.
        for prestige_building in self.game_element.buildings:
            if prestige_building.get_building_type() == BuildingType.PRESTIGE:
                prestige_building.color_player = None
        # Setup buildings with prestige buildings.
        self.current_buildings = [prestige_building for prestige_building in self.game_element.buildings
                                  if prestige_building.get_building_type() == BuildingType.PRESTIGE
                                  and (prestige_building.belongs_to_beginner_version or not self.version.is_beginner())]
        # Setup buildings with background player buildings.
        for player in self.players:
            self.current_buildings.extend([background_player_building
                                           for background_player_building in self.game_element.buildings
                                           if background_player_building.get_building_type() == BuildingType.BACKGROUND
                                           and background_player_building.color_player == player.color_player
                                           and (background_player_building.belongs_to_beginner_version
                                                or not self.version.is_beginner())])
        # Setup the road (without worker) and the neutral buildings.
        neutral_buidings = [neutral_buiding for neutral_buiding in NeutralBuilding.neutral_buildings.values()
                            if neutral_buiding != self.game_element.last_neutral_building
                            and (neutral_buiding.belongs_to_beginner_version or not self.version.is_beginner())
                            ]  # type: List[NeutralBuilding]
        random.shuffle(neutral_buidings)
        self.road = [[neutral_building, None] for neutral_building in
                     neutral_buidings[:self.game_element.n_all_except_last_neutral_buildings[self.n_players]]] + \
                    [[self.game_element.last_neutral_building, None]]
        self.current_buildings.extend(building_worker[0] for building_worker in self.road)
        # Setup the Provost.
        self.i_provost = ([building_worker[0] for building_worker in self.road].index(self.game_element.place_provost)
                          if not self.version.is_beginner() else None)
        # Setup the castle.
        for castle_part in self.game_element.castle:
            castle_part.setup(self.n_players)
        # Setup the passing marker players.
        self.passing_marker_players = list()
        # Reinitialize the player for each color of the players.
        for color_player in ColorPlayer.colors_players.values():
            color_player.player = None
        # Setup the first player.
        self.i_first_player = 0
        # Setup the players (excepted their decks).
        for player in self.players:
            player.setup()
        # Setup the decks (cards into: pile, hand, discard) of the players and the buildings.
        for player in self.players:
            # Initialize the deck with all player buildings.
            player.deck = {player_building: Location.PILE for player_building in self.game_element.buildings
                           if player_building.get_building_type() == BuildingType.PLAYER
                           and player_building.color_player == player.color_player
                           and (player_building.belongs_to_beginner_version or not self.version.is_beginner())}
            # Setup the number of cubes into the area for all small production player buildings.
            for small_production_player_building in player.deck:
                if small_production_player_building.name.startswith('Small'):
                    small_production_player_building.setup(self.n_players)
            # Add the deck to buildings.
            self.current_buildings.extend(player.deck.keys())
            # Set the hand. The player can discard the hand for a new one.
            self.setup_player_buildings_from_pile_to_hand(player, self.game_element.n_cards_in_hand)
            n_possibilities_to_discard_cards = self.game_element.n_possibilities_to_discard_cards  # type: int
            while n_possibilities_to_discard_cards > 0 and player.choose_discard_hand_for_new():
                player.move_all_buildings_from_to_location(Location.HAND, Location.DISCARD)
                self.setup_player_buildings_from_pile_to_hand(player, self.game_element.n_cards_in_hand)
                n_possibilities_to_discard_cards -= 1
        # Display the deck of the human player just before the start of the game.
        [player for player in self.players if player.is_human()][0].print_buildings_by_location(0)
        # End of the setup for a game.
        print('Setup for a game: ' +
              'version "' + self.version.name + '", ' +
              str(len(self.current_buildings)) + ' buildings for the game, ' +
              str(len(self.road)) + ' buildings on the road, ' +
              str(len(self.players)) + ' players.')

    def setup_player_buildings_from_pile_to_hand(self, player: Player, n_cards_pile_to_hand: int) -> None:
        """Setup of the game for the player buildings of a player moving from the pile to the hand."""
        player_buildings_pile = player.get_player_buildings_by_location(Location.PILE)  # type: List[PlayerBuilding]
        random.shuffle(player_buildings_pile)
        for player_building in player_buildings_pile[:n_cards_pile_to_hand]:
            player.deck[player_building] = Location.HAND

    def play(self) -> None:
        """Play one game."""
        print('The game starts.')
        n_turns = 0  # type: int # Number of turns.
        while not self.game_ended():
            n_turns += 1
            self.print_turn_begin(n_turns)
            self.play_phase_income()
            self.play_phase_actions()
            self.play_phase_provost_movements()
            self.play_phase_building_effects()
            self.play_phase_castle()
            self.play_phase_end_turn()
        print('The game ends.')
        self.winners()

    def play_phase_income(self) -> None:
        """
        Each player gets 2 deniers from the stock.
        [Standard version] Furthermore, each player also gets 1 denier per residential building (green background) they own along the road.
        [Standard version] Finally, if a player has built the Hotel, they get 1 more denier from the stock.
        """
        income_phase = self.get_print_phase_begin(1)  # type: Phase
        if income_phase.belongs_to_beginner_version or not self.version.is_beginner():
            # Each player gets deniers from the stock.
            for player in self.players:
                print(indent(2) + player.name() +
                      ' obtains ' + str(income_phase.n_deniers) + ' ' + Money.money.name + '(s).')
                player.current_money_resources[Money.money] += income_phase.n_deniers
            # Deniers for residential player buildings and hotel prestige building on the road.
            print(indent(2) + 'The road consists in: ' + self.txt_road(False) + '.')
            if not self.version.is_beginner():
                for building_worker in self.road:
                    building_worker[0].income_effect(income_phase)
            # Display the players.
            print(indent(2) + 'Players (according to the order in the game):')
            for player in self.players:
                print(indent(3) +
                      player.txt_name_money_resources_workers_PPs_deck(True, True, False, True, False) + '.')

    def play_phase_actions(self) -> None:
        """
        Starting with the first player and then following in clockwise order, the players must pick one of the following actions:
        A) Pick a card
        The player pays 1 denier to the stock to take the first card on their pile and add it to their hand. If there are no cards left in the pile, the player shuffles the cards of their discard pile and builds a new pile.
        The number of cards a player may have in their hand is not limited.
        B) Replace all the cards in your hand
        The player pays 1 denier to the stock to discard all the cards in their hand (the player must get rid of them all), place them face up in the discard pile, and take the same number of cards from their pile. If there is not enough cards left in the pile, the player shuffles the cards of their discard pile and builds a new pile.
        C) Place a worker on a building
        The player pays 1 denier to the stock and places 1 worker on a card along the road. There can be only 1 worker per card. A player may place a worker on a neutral building, on one of their own buildings, or on a building belonging to someone else.
        Placing a worker on a residential building or a prestige building is forbidden.
        D) Construct a building from your hand
        The player takes a card from their hand, pays its cost (indicated in the top left-hand corner) to the stock, and adds the building at the end of the road. From this point on, the players may place a worker on the building when the time comes for them to choose an action.
        E) Construct a prestige building
        The player chooses a prestige building among those that are still available, pays its cost (indicated in the top left-hand corner of the card) to the stock, and places the prestige building ...
            [Beginner version] ... before them (the building is NOT added to the end of the road).
            [Standard version] ... on top of one of their own residential buildings.
        [Standard version] From now on, this residential building does not yield any income during phase 1.
        [Standard version] Remark: It is impossible to build a prestige building if you do not own any residential buildings.
        F) Passing
        The player puts their passing marker on the space of the bridge with the lowest number. The first player who passes gets 1 denier from the stock.
        Once a player has passed, they cannot take any actions for the remainder of the phase.
        Phase 2 lasts until all players have passed.
        """
        actions_phase = self.get_print_phase_begin(2)  # type: Phase
        if actions_phase.belongs_to_beginner_version or not self.version.is_beginner():
            # Display the available prestige buildings.
            print(indent(2) + 'The available prestige buildings are: ' +
                  self.txt_available_prestige_buildings(True) + '.')
            # Display the road.
            print(indent(2) + 'The road consists in: ' + self.txt_road(False) + '.')
            # Order all the players.
            self.passing_marker_players = list()
            current_turn_players = self.players[self.i_first_player:] + \
                                   self.players[:self.i_first_player]  # type: List[Player]
            # Display the players in the order they play this turn.
            print(indent(2) + 'Players (in the order they play this turn):')
            for player in current_turn_players:
                print(indent(3) +
                      player.txt_name_money_resources_workers_PPs_deck(True, True, True, False, True) + '.')
            # Start the phase for all the players.
            i_current_turn_players = 0  # type: int
            while current_turn_players:
                # Current player to play.
                player = current_turn_players[i_current_turn_players]  # type: Player
                print(indent(2) + 'The current player' +
                      player.txt_name_money_resources_workers_PPs_deck(True, True, True, True, True) + '.')
                # The current player chooses one action in all his/her possible actions.
                player_action_chosen = player.choose_action(self.possible_actions(actions_phase, player))
                if player_action_chosen[0] == Action.PASSING:
                    # The current player passes.
                    print(indent(3) + player.name() + ' passes his/her turn.')
                    if not self.passing_marker_players:
                        # Bonus for the first player passing.
                        resource_gain, qty_gain = Money.money, actions_phase.n_deniers_for_first_player_passing  # type: MoneyResource, int
                        print(indent(3) + player.name() + ' is the first player to pass his/her turn and obtains ' +
                              str(qty_gain) + ' ' + resource_gain.name + '(s).')
                        player.current_money_resources[resource_gain] += qty_gain
                    print(indent(3) +
                          player.txt_name_money_resources_workers_PPs_deck(True, True, True, False, False) +
                          ' once he/she had passed.')
                    self.passing_marker_players.append(player)  # The current player goes on the bridge.
                    del current_turn_players[i_current_turn_players]  # The current player is out for this turn.
                    # Next player.
                    if i_current_turn_players == len(current_turn_players):
                        i_current_turn_players = 0
                    else:
                        pass  # The next player is in the position of the current player who passes.
                else:
                    # The current player doesn't pass ; we do the action chosen he/she had chosen.
                    self.do_player_action_chosen(actions_phase, player, player_action_chosen)
                    # Next player.
                    if i_current_turn_players == len(current_turn_players) - 1:
                        i_current_turn_players = 0
                    else:
                        i_current_turn_players += 1

    def possible_actions(self, actions_phase: Phase, player: Player):  # -> List[[Action, str, "parameters"]]
        """List all the possible actions of the player. The list must contain passing action."""
        possible_actions = [[Action.PASSING, Action.PASSING.txt + '.']]  # type: List[List[Action, str, ...]]
        # Action: Pick a card.
        if player.current_money_resources[Money.money] + actions_phase.n_deniers_to_take_a_card >= 0 \
                and (len(player.get_player_buildings_by_location(Location.PILE)) +
                     len(player.get_player_buildings_by_location(Location.DISCARD))) >= 1:
            # The player must pay for an existing card to move from the pile (or from the discard if the pile is empty) to the hand.
            possible_actions.append([Action.PICK_CARD, Action.PICK_CARD.txt + '.'])
        # Action: Replace all the cards in your hand.
        if player.current_money_resources[Money.money] + actions_phase.n_deniers_to_discard_all_cards >= 0 \
                and len(player.get_player_buildings_by_location(Location.HAND)) >= 1 \
                and (len(player.get_player_buildings_by_location(Location.PILE)) +
                     len(player.get_player_buildings_by_location(Location.DISCARD))) >= 1:
            # The player must pay for existing cards to move from the pile or from the discard to the hand.
            possible_actions.append([Action.REPLACE_CARDS_IN_HAND, Action.REPLACE_CARDS_IN_HAND.txt + '.'])
        # Action: Place a worker on a building.
        if player.current_money_resources[Money.money] + actions_phase.n_deniers_to_place_a_worker >= 0 \
                and player.current_n_workers + actions_phase.n_workers >= 0:
            for i_road, building_worker in enumerate(self.road):
                if building_worker[0].allows_to_place_a_worker and building_worker[1] is None:
                    possible_actions.append([Action.PLACE_WORKER_ON_BUILDING,
                                             Action.PLACE_WORKER_ON_BUILDING.txt + ' namely a ' +
                                             building_worker[0].txt_name_owner(True) + ' which is the ' +
                                             ordinal_number(i_road + 1) + ' building along the road.',
                                             i_road])
        # Action: Construct a building from your hand.
        for player_building in player.get_player_buildings_by_location(Location.HAND):
            for resource_payments in player.resource_all_payments(player_building.resource_costs):
                possible_actions.append([Action.CONSTRUCT_BUILDING_FROM_HAND,
                                         Action.CONSTRUCT_BUILDING_FROM_HAND.txt + ' namely a ' +
                                         player_building.name + ' added at the end of the road by consuming ' +
                                         TXT_SEPARATOR.join(str(qty) + ' ' + resource.name + '(s)'
                                                            for resource, qty in resource_payments.items() if qty < 0) +
                                         '.',
                                         player_building,
                                         resource_payments])
        # Action: Construct a prestige building.
        if self.version.is_beginner():
            for prestige_building in self.get_available_prestige_buildings():
                for resource_payments in player.resource_all_payments(prestige_building.resource_costs):
                    possible_actions.append([Action.CONSTRUCT_PRESTIGE_BUILDING_BEGINNER,
                                             Action.CONSTRUCT_PRESTIGE_BUILDING_BEGINNER.txt + ' namely a ' +
                                             prestige_building.name + ' by consuming ' +
                                             TXT_SEPARATOR.join(str(qty) + ' ' + resource.name + '(s)'
                                                                for resource, qty in resource_payments.items()
                                                                if qty < 0) + ' and' +
                                             ' giving ' + str(prestige_building.n_prestige_pts) + ' prestige point(s).',
                                             prestige_building,
                                             resource_payments])
        else:
            for i_road, building_worker in enumerate(self.road):
                # Is it a background player building (that is a residential building, the only buildings which can be a prestige building) and is it owned by the player?
                if building_worker[0].can_be_a_prestige_building \
                        and building_worker[0].color_player == player.color_player:
                    # The player chooses a prestige building among those that are still available.
                    for prestige_building in self.get_available_prestige_buildings():
                        # The player pays the cost of the prestige building.
                        for resource_payments in player.resource_all_payments(prestige_building.resource_costs):
                            possible_actions.append([Action.CONSTRUCT_PRESTIGE_BUILDING_STANDARD,
                                                     Action.CONSTRUCT_PRESTIGE_BUILDING_STANDARD.txt + ' namely a ' +
                                                     prestige_building.name +
                                                     ' replacing the ' + ordinal_number(i_road + 1) +
                                                     ' building (a residential building which you have) along the road by consuming ' +
                                                     TXT_SEPARATOR.join(str(qty) + ' ' + resource.name + '(s)'
                                                                        for resource, qty in resource_payments.items()
                                                                        if qty < 0) + ' and' +
                                                     ' giving ' + str(prestige_building.n_prestige_pts) +
                                                     ' prestige point(s).',
                                                     i_road,
                                                     prestige_building,
                                                     resource_payments])
        # Return all possible actions.
        return possible_actions

    def do_player_action_chosen(self, actions_phase: Phase, player: Player, player_action_chosen):
        """Do the action chosen by the player (excepted passing)."""
        action_chosen = player_action_chosen[0]  # type: Action
        txt_action_chosen = player_action_chosen[1]  # type: str
        print(indent(3) + player.name() + ' chooses the action: ' + txt_action_chosen)
        if action_chosen == Action.PICK_CARD:
            # Action: Pick a card.
            player.current_money_resources[Money.money] += actions_phase.n_deniers_to_take_a_card
            if not player.get_player_buildings_by_location(Location.PILE):
                player.move_all_buildings_from_to_location(Location.DISCARD, Location.PILE)
            self.setup_player_buildings_from_pile_to_hand(player, 1)
            if player.is_human():
                player.print_buildings_by_location(3)
        elif action_chosen == Action.REPLACE_CARDS_IN_HAND:
            # Action: Replace all the cards in your hand.
            player.current_money_resources[Money.money] += actions_phase.n_deniers_to_discard_all_cards
            player_buildings_hand = player.get_player_buildings_by_location(Location.HAND)  # type: List[PlayerBuilding]
            n_cards_to_replace = len(player_buildings_hand)  # type: int
            for player_building_hand_to_discard in player_buildings_hand:
                player.deck[player_building_hand_to_discard] = Location.DISCARD
            self.setup_player_buildings_from_pile_to_hand(player, n_cards_to_replace)
            n_cards_to_replace -= len(player.get_player_buildings_by_location(Location.HAND))
            if n_cards_to_replace > 0:
                # It remains cards to move all cards from discard to pile and then to move some cards from pile to hand.
                player.move_all_buildings_from_to_location(Location.DISCARD, Location.PILE)
                self.setup_player_buildings_from_pile_to_hand(player, n_cards_to_replace)
            if player.is_human():
                player.print_buildings_by_location(3)
        elif action_chosen == Action.PLACE_WORKER_ON_BUILDING:
            # Action: Place a worker on a building.
            player.current_money_resources[Money.money] += actions_phase.n_deniers_to_place_a_worker
            player.current_n_workers += actions_phase.n_workers
            i_road = player_action_chosen[2]  # type: int
            self.road[i_road][1] = player
            print(indent(3) + 'The new road consists in: ' + self.txt_road(False) + '.')
        elif action_chosen == Action.CONSTRUCT_BUILDING_FROM_HAND:
            # Action: Construct a building from your hand.
            player_building = player_action_chosen[2]  # type: PlayerBuilding
            player.deck[player_building] = Location.ROAD
            self.road.append([player_building, None])
            resource_payments = player_action_chosen[3]  # type: Dict[Resource, int]
            for resource, qty in resource_payments.items():
                player.current_money_resources[resource] += qty
            if player.is_human():
                player.print_buildings_by_location(3)
            print(indent(3) + 'The new road consists in: ' + self.txt_road(False) + '.')
        elif action_chosen == Action.CONSTRUCT_PRESTIGE_BUILDING_BEGINNER:
            # Action: Construct a prestige building [beginner version].
            prestige_building = player_action_chosen[2]  # type: PrestigeBuilding
            prestige_building.color_player = player.color_player
            player.current_n_prestige_pts += prestige_building.n_prestige_pts  # PPs are added only for beginner version.
            resource_payments = player_action_chosen[3]  # type: Dict[Resource, int]
            for resource, qty in resource_payments.items():
                player.current_money_resources[resource] += qty
            print(indent(3) + 'The remaining available prestige buildings are: ' +
                  self.txt_available_prestige_buildings(False) + '.')
        elif action_chosen == Action.CONSTRUCT_PRESTIGE_BUILDING_STANDARD:
            # Action: Construct a prestige building [standard version].
            i_road = player_action_chosen[2]  # type: int
            prestige_building = player_action_chosen[3]  # type: PrestigeBuilding
            prestige_building.color_player = player.color_player
            self.road[i_road][0] = prestige_building  # Replace the residential building by the prestige building.
            resource_payments = player_action_chosen[4]  # type: Dict[Resource, int]
            for resource, qty in resource_payments.items():
                player.current_money_resources[resource] += qty
            print(indent(3) + 'The remaining available prestige buildings are: ' +
                  self.txt_available_prestige_buildings(False) + '.')
            print(indent(3) + 'The new road consists in: ' + self.txt_road(True) + '.')
        else:
            raise Exception('Action ' + str(player_action_chosen) + ' unknown.')
        print(indent(3) + player.txt_name_money_resources_workers_PPs_deck(True, True, True, True, True) +
              ' once the action done.')

    def play_phase_provost_movements(self) -> None:
        """
        [Standard version] Following the passing order of phase 2 (that is, according to the increasing numbers on the bridge), the players now have the opportunity to move the Provost along the road by paying deniers. The price is 1 denier per card; each player may pay up to 3 deniers.
        [Standard version] Remark: The Provost may not move beyond the limits of the road.
        [Standard version] There is only one turn to move the Provost. Once everyone has had an opportunity to move him, the phase is over.
        """
        provost_movement_phase = self.get_print_phase_begin(3)  # type: Phase
        if provost_movement_phase.belongs_to_beginner_version or not self.version.is_beginner():
            # Display the road.
            print(indent(2) + 'The road consists in: ' + self.txt_road(False) + '.')
            # Turns to move the Provost.
            for i_turn_to_move_provost in range(provost_movement_phase.n_turns_to_move_provost):
                # Display the players on the bridge that is according the order of the passing marker players.
                print(indent(2) + 'Players on the bridge (that is according the order of the passing marker players):')
                for player in self.passing_marker_players:
                    print(indent(3) +
                          player.txt_name_money_resources_workers_PPs_deck(True, False, False, False, False) + '.')
                # The players have the opportunity to move the Provost along the road by paying deniers.
                for player in self.passing_marker_players:
                    # The player.
                    print(indent(2) +
                          player.txt_name_money_resources_workers_PPs_deck(True, False, False, False, False) +
                          ' and maybe he/she can move the Provost.')
                    # Provost's location on the road.
                    print(indent(3) + self.txt_provost_owner_building() + '.')
                    # Minimum and maximum possible Provost's movements for the player.
                    n_max_provost_movements_player_limited_by_money = int(player.current_money_resources[Money.money] /
                                                                          -provost_movement_phase.n_deniers_per_a_provost_movement)
                    n_min_provost_movements_player = max(-self.i_provost,
                                                         -provost_movement_phase.n_max_provost_movements_per_player,
                                                         -n_max_provost_movements_player_limited_by_money)
                    n_max_provost_movements_player = min(len(self.road) - 1 - self.i_provost,
                                                         +provost_movement_phase.n_max_provost_movements_per_player,
                                                         +n_max_provost_movements_player_limited_by_money)
                    if n_min_provost_movements_player == n_max_provost_movements_player:
                        print(indent(3) + player.name() + ' can\'t move the Provost.')
                    else:
                        # The player has the opportunity to move the Provost.
                        print(indent(3) + player.name() + ' can move the Provost from ' +
                              str(n_min_provost_movements_player) + ' to ' + str(n_max_provost_movements_player) +
                              ' along the road.')
                        n_provost_movement = player.choose_n_provost_movement(n_min_provost_movements_player,
                                                                              n_max_provost_movements_player)  # type: int
                        if n_provost_movement == 0:
                            print(indent(3) + player.name() + ' doesn\'t want to move the Provost along the road.')
                        else:
                            print(indent(3) + player.name() + ' moves the Provost by ' + str(n_provost_movement) +
                                  ' along the road.')
                            self.i_provost += n_provost_movement
                            player.current_money_resources[Money.money] += abs(n_provost_movement) * \
                                                                           provost_movement_phase.n_deniers_per_a_provost_movement

    def play_phase_building_effects(self) -> None:
        """
        [Standard version] Buildings are activated in order, starting at the beginning of the road, up to and including the building card the Provost is now occupying.
        ● A building without a worker is not activated.
        ● A building with a worker on it has a primary effect profiting the owner of the worker, then a secondary effect profiting the owner of the building.
        ● If a player has placed a worker on one of their own buildings, they only take advantage of the building’s primary effect; the player may not choose the secondary effect.
        ● [Standard version] The buildings beyond the Provost’s current location have no effect.
        The players get their workers back.
        Remark: The players do not have to use the effect (either primary or secondary) of a building. The owner of a building may use its secondary effect even if the worker’s owner chose not to use the primary effect.
        """
        effects_building_phase = self.get_print_phase_begin(4)  # type: Phase
        # Display the road.
        print(indent(2) + 'The road consists in: ' + self.txt_road(False) + '.')
        # Display the players.
        print(indent(2) + 'Players (according to the order in the game):')
        for player in self.players:
            print(indent(3) + player.txt_name_money_resources_workers_PPs_deck(True, True, True, True, True) + '.')
        # Display the road.
        if effects_building_phase.belongs_to_beginner_version or not self.version.is_beginner():
            if not self.version.is_beginner():
                print(indent(2) + self.txt_provost_owner_building() + '.')
            for i_road, building_worker in enumerate(self.road):
                # Retrieve the worker of a player.
                worker = building_worker[1]  # type: Player
                # Display the building to apply along the road.
                print(indent(2) + 'Apply the ' + ordinal_number(i_road + 1) + ' building along the road: ' +
                      self.txt_one_building_worker_road(self.road[i_road], False) + '.')
                # Retrieve the building.
                building = None  # type: Building
                if len(building_worker) == 2:
                    # building_worker := Tuple[(neutral or player) building, worker]
                    building = building_worker[0]
                else:
                    # building_worker := Tuple[(background player or prestige) building, worker, (neutral or player) building]
                    building = building_worker[2]
                    self.road[i_road] = self.road[i_road][:2]  # Remove (the 3rd that is) the last element.
                # Apply eventually the effect(s).
                if worker is not None:
                    if self.version.is_beginner() or i_road <= self.i_provost:
                        building.apply_primary_effect(worker)
                        if building.get_building_type() == BuildingType.PLAYER:
                            if worker != building.color_player.player:
                                building.apply_secondary_effect()
                            else:
                                print(indent(3) +
                                      'We can\'t apply the secondary effect of the building because the worker is placed on one of his/her own building and already took advantage of the building\'s primary effect.')
                    else:
                        print(indent(3) +
                              'The worker in the building can\'t apply the effect because he/she is beyond the Provost\'s current location.')
                    # The worker goes from the road to the player.
                    self.road[i_road][1] = None
                    worker.current_n_workers += 1

    def play_phase_castle(self) -> None:
        """
        Following the passing order, the players may offer batches to the castle (if they want to). A batch is composed of 3 resources: 1 food, 1 wood and 1 stone. Each player gives the stock their cubes accordingly and takes as many point tokens as they have given batches.
        Prestige point tokens are taken according to a certain order: first those of the Dungeon (red tokens), then those of the Walls (orange tokens) and finally those of the Towers (yellow tokens). A player may earn tokens of different colors in the same turn.
        A player cannot offer more batches than there are prestige point tokens left in the stock. So, it is possible for a player to have some batches left.
        The player who has offered the most batches during this phase takes 1 gold cube from the stock.
        In case of a draw, the player who offered that number of batches first wins the cube.
        If no-one has offered any batch during this phase, 2 tokens are removed from the stock of victory points - these tokens are removed from the game. As was the case for building, these tokens are taken from the proper section of the Castle (red, then orange, then yellow).
        If no token is left in the stock, the game is over.
        """
        castle_phase = self.get_print_phase_begin(5)  # type: Phase
        if castle_phase.belongs_to_beginner_version or not self.version.is_beginner():
            # Display the players on the bridge that is according the order of the passing marker players.
            print(indent(2) + 'Players on the bridge (that is according the order of the passing marker players):')
            for player in self.passing_marker_players:
                print(indent(3) +
                      player.txt_name_money_resources_workers_PPs_deck(False, True, False, False, False) + '.')
            # The players may offer batches to the castle.
            player_offers_most_batches = None  # type: Player
            n_most_batches_offered = 0  # type: int
            for player in self.passing_marker_players:
                # The player.
                print(indent(2) +
                      player.txt_name_money_resources_workers_PPs_deck(False, True, False, False, False) +
                      ' and maybe he/she can offer batches to the castle.')
                # Display the tokens in the castle.
                if self.get_remaining_n_castle_tokens() == 0:
                    print(indent(3) + 'There are not tokens anymore in the castle.')
                else:
                    print(indent(3) + 'The tokens in the castle are: ' +
                          TXT_SEPARATOR.join(str(castle.current_n_castle_tokens) + ' of ' + str(castle.n_prestige_pts) +
                                             ' prestige point(s) (' + castle.name + ')'
                                             for castle in self.game_element.castle
                                             if castle.current_n_castle_tokens > 0)
                          + '.')
                # The player offer batches to the castle.
                n_max_batches_to_castle_player = min(player.n_max_batches_to_castle(castle_phase),
                                                     self.get_remaining_n_castle_tokens())  # type: int
                if n_max_batches_to_castle_player == 0:
                    print(indent(3) + player.name() + ' can\'t offer batch to the castle.')
                else:
                    print(indent(3) + player.name() + ' can offer 0 to ' + str(n_max_batches_to_castle_player) +
                          ' batch(es) to the castle.')
                    n_batches_offered_to_castle_player = player.choose_n_batches_to_castle(
                        n_max_batches_to_castle_player)  # type: int
                    if n_batches_offered_to_castle_player == 0:
                        print(indent(3) + player.name() + ' doesn\'t offer batch to the castle.')
                    else:
                        print(indent(3) + player.name() + ' offers ' + str(n_batches_offered_to_castle_player) +
                              ' batch(es) to the castle.')
                        player.consume_n_max_batches_to_castle(n_batches_offered_to_castle_player, castle_phase)
                        player.current_n_prestige_pts += self.remove_tokens_castle(n_batches_offered_to_castle_player)
                        if n_batches_offered_to_castle_player > n_most_batches_offered:
                            player_offers_most_batches = player
                            n_most_batches_offered = n_batches_offered_to_castle_player
            # Is there a player who offered most batches to the castle?
            if player_offers_most_batches is None:
                # If no-one has offered any batch, tokens are removed from the stock of victory points.
                print(indent(2) + 'No-one has offered any batch; tokens are removed.')
                self.remove_tokens_castle(castle_phase.n_prestige_pt_tokens_to_remove)  # PPs are lost!
            else:
                # The player who has offered the most batches during this phase takes gold cube(s) from the stock.
                print(indent(2) + player_offers_most_batches.name() +
                      ' offered the most batches and takes gold cube(s).')
                player_offers_most_batches.current_money_resources[
                    Resource.get_wild_resource()] += castle_phase.n_gold_cubes_for_player_offered_most_batches

    def play_phase_end_turn(self) -> None:
        """
        [Standard version] The Provost advances by 2 cards toward the end of the road. If there is only 1 card before the end of the road, the Provost only advances by 1 card. If the Provost is already at the end of the road, the Provost does not move.
        The first player card is passed to the player to the left of the current first player, and a new turn begins.
        """
        end_turn_phase = self.get_print_phase_begin(6)  # type: Phase
        if end_turn_phase.belongs_to_beginner_version or not self.version.is_beginner():
            if not self.version.is_beginner():
                # The Provost advances toward the end of the road.
                self.i_provost = min(self.i_provost + end_turn_phase.n_provost_advances, len(self.road) - 1)
                print(indent(2) + self.txt_provost_owner_building() + '.')
            # The first player card is passed to the player to the left of the current first player.
            if self.i_first_player == self.n_players - 1:
                self.i_first_player = 0
            else:
                self.i_first_player += 1
            print(indent(2) + 'The new first player is ' + self.players[self.i_first_player].name() + '.')

    def winners(self) -> None:
        """The player with the most prestige points is the winner. There is no tie-breaker."""
        # Display the players.
        print(indent(0) + 'Players (according to the order in the game):')
        for player in self.players:
            print(indent(1) + player.txt_name_money_resources_workers_PPs_deck(True, True, False, True, True) + '.')
        # Display the road.
        print(indent(0) + 'The road consists in: ' + self.txt_road(True) + '.')
        # We don't use a dictionary in order to keep the order of self.players.
        tot_n_prestige_pts_players = [player.tot_n_prestige_pts([building_worker[0] for building_worker in self.road
                                                                 if building_worker[0].get_building_type() in [
                                                                     BuildingType.BACKGROUND, BuildingType.PLAYER,
                                                                     BuildingType.PRESTIGE]
                                                                 and building_worker[0].color_player.player == player])
                                      for player in self.players]  # type: List[int]
        print('The number of prestige points of players are: ' +
              TXT_SEPARATOR.join(str(tot_n_prestige_pts_players[i_player]) + ' for ' + self.players[i_player].name()
                                 for i_player in range(self.n_players)) + '.')
        max_tot_n_prestige_pts = max(tot_n_prestige_pts_players)
        print('The winner(s) is(are): ' +
              TXT_SEPARATOR.join(self.players[i_player].name() for i_player in range(self.n_players)
                                 if tot_n_prestige_pts_players[i_player] == max_tot_n_prestige_pts) + '.')

    def print_turn_begin(self, n_turns: int) -> None:
        """Print the beginning of a turn."""
        print(indent(0) + 'Turn ' + str(n_turns) + '.')
        print(indent(1) + 'The first player is ' + self.players[self.i_first_player].name() + '.')

    def get_print_phase_begin(self, phase_numero: int) -> Phase:
        """Print the beginning of a phase of a turn and get the phase."""
        phase = self.game_element.phases[phase_numero]
        print(indent(1) + 'Phase "' + phase.name + '".')
        return phase

    def remove_tokens_castle(self, n_prestige_pt_tokens_to_remove: int) -> int:
        """Remove prestige point tokens in the castle and return the corresponding prestige points."""
        n_prestige_pts = 0  # type: int
        for castle_part in self.game_element.castle:
            # It is possible to break of this loop if n_prestige_pt_tokens_to_remove == 0.
            n_prestige_pt_tokens_to_remove_castle_part = min(castle_part.current_n_castle_tokens,
                                                             n_prestige_pt_tokens_to_remove)
            if n_prestige_pt_tokens_to_remove_castle_part > 0:  # One can delete this test because -= 0 is an identity!
                castle_part.current_n_castle_tokens -= n_prestige_pt_tokens_to_remove_castle_part
                n_prestige_pts += n_prestige_pt_tokens_to_remove_castle_part * castle_part.n_prestige_pts
                n_prestige_pt_tokens_to_remove -= n_prestige_pt_tokens_to_remove_castle_part
        # Remark: n_prestige_pt_tokens_to_remove can be still > 0 (if we have already remove all possible tokens).
        return n_prestige_pts

    def txt_road(self, with_prestige_points: bool) -> str:
        """Get the text of the road with the prestige points."""
        return TXT_SEPARATOR.join(self.txt_one_building_worker_road(building_worker, with_prestige_points)
                                  for building_worker in self.road)

    def txt_one_building_worker_road(self, building_worker, with_prestige_points: bool) -> str:
        """Get the text of one building and worker on the road with the prestige points."""
        return (building_worker[0].txt_name_owner(True)
                if len(building_worker) == 2 else building_worker[2].txt_name_owner(True) + ' constructed as a ' +
                                                  building_worker[0].txt_name_owner(True)) + \
               (' where is a worker ' + building_worker[1].name() if building_worker[1] is not None else '') + \
               (' giving ' + str(building_worker[0].n_prestige_pts) + ' prestige point(s)'
                if with_prestige_points and building_worker[0].n_prestige_pts > 0 else '')

    def get_available_prestige_buildings(self):  # -> List[PrestigeBuilding]
        """Get the available prestige buildings."""
        return [prestige_building for prestige_building in self.current_buildings
                if prestige_building.get_building_type() == BuildingType.PRESTIGE
                and prestige_building.color_player is None]

    def txt_available_prestige_buildings(self, with_prestige_points: bool) -> str:
        """Get the text of the available prestige buildings with the prestige points."""
        return TXT_SEPARATOR.join(prestige_building.name + (' giving ' + str(prestige_building.n_prestige_pts) +
                                                            ' prestige point(s)' if with_prestige_points else '')
                                  for prestige_building in self.get_available_prestige_buildings())

    def txt_provost_owner_building(self) -> str:
        """Get the text of the Provost location in the building with its owner (a player)."""
        return 'The Provost is in the ' + ordinal_number(self.i_provost + 1) + ' building along the road, namely ' + \
               self.road[self.i_provost][0].txt_name_owner(True)

    def get_remaining_n_castle_tokens(self) -> int:
        """Get the remaining number of tokens in the castle."""
        return sum([castle_part.current_n_castle_tokens for castle_part in self.game_element.castle])

    def game_ended(self) -> bool:
        """Is the game ended?"""
        """
        The game ends at the end of the turn when the stock has run out of prestige point tokens.
        """
        return self.get_remaining_n_castle_tokens() == 0


@unique
class Action(Enum):
    """Enumeration of all the possible actions of the phase Actions."""
    PICK_CARD = ('Pick a card')
    REPLACE_CARDS_IN_HAND = ('Replace all the cards in your hand')
    PLACE_WORKER_ON_BUILDING = ('Place a worker on a building')
    CONSTRUCT_BUILDING_FROM_HAND = ('Construct a building from your hand')
    CONSTRUCT_PRESTIGE_BUILDING_BEGINNER = ('Construct a prestige building (Beginner version)')
    CONSTRUCT_PRESTIGE_BUILDING_STANDARD = ('Construct a prestige building (Standard version)')
    PASSING = ('Passing')

    def __init__(self, txt: str):
        """Initialization of an action."""
        self.txt = txt  # Type: str


class GameElement:
    """Elements of the game Caylus Magna Carta."""

    TXT_IS_NOT_CORRECT = 'isn\'t correct'  # type: str

    def __init__(self):
        """Initialization of the elements of the game."""
        # WARNING: for all buildings, read from the XML file:
        #           <effect>, <primary_effect>, <secondary_effect>: <cost> and <gain>, <CHOICES>
        #           <construction>: <text> and <where>
        #           ... <CHOICES>, <CHOICE>.
        # Attributes obtained from the XML file.
        self.game_name = None  # type: str # Name of the game.
        self.n_min_players = None  # type: int # Minimal number of players.
        self.n_max_players = None  # type: int # Maximal number of players.
        self.n_cards_in_hand = None  # type: int
        self.game = None  # type: Game
        self.versions = None  # type: List[Version]
        self.color_players = None  # type: List[ColorPlayer]
        self.castle = None  # type: List[Castle]
        self.money = None  # type: Money
        self.resources = None  # type: List[Resource]
        self.phases = None  # type: List[Phase]
        self.buildings = None  # type: List[Building]
        self.last_neutral_building = None  # type: NeutralBuilding # Place the Peddler card on the table.
        self.place_provost = None  # type: NeutralBuilding # The Provost pawn is placed on the peddler card.
        self.n_all_except_last_neutral_buildings = None  # type: List[int] # Place 1 card (2 player games), 2 cards (3 player games) or 3 cards (4 player games) to the left of the Peddler.
        self.n_cards_in_hand = None  # type: int# Each player takes 3 cards from their own pile.
        self.n_possibilities_to_discard_cards = None  # type: int # Each player may discard all the cards in their hand and take 3 new cards. This may only be done once.
        # Check if there is enough arguments, at least the XML file.
        n_args = len(sys.argv)  # type: int
        if n_args < 2:
            self.usage('The number of arguments ' + str(n_args) + ' ' + GameElement.TXT_IS_NOT_CORRECT +
                       ' (you must have an XML file).')
        # Check if the XML file exists.
        if not path.isfile(sys.argv[1]):
            self.usage('The file ' + sys.argv[1] + ' does not exist.')
        xml_tree = ET.parse(sys.argv[1])  # type: xml.etree.ElementTree.ElementTree
        xml_tree_root = xml_tree.getroot()  # type: xml.etree.ElementTree.Element
        # Read the number minimum and maximum of players from the XML file.
        self.n_min_players = int(xml_tree_root.find('n_min_players').text)
        self.n_max_players = int(xml_tree_root.find('n_max_players').text)
        txt_n_min_max_players = str(self.n_min_players) + '..' + str(self.n_max_players)  # type: str
        # Check the number of arguments according to the number of players.
        if not (3 + self.n_min_players <= n_args <= 3 + self.n_max_players):
            self.usage('The number of arguments ' + str(n_args) + ' ' + GameElement.TXT_IS_NOT_CORRECT + '.',
                       txt_n_min_max_players)
        # Read the versions from the XML file.
        self.versions = list()
        for version_name_tag in xml_tree_root.findall('versions/version/name'):
            self.versions.append(Version(version_name_tag.text))
        # Check the version.
        if sys.argv[2] not in [version.name for version in self.versions]:
            self.usage('The version ' + sys.argv[2] + ' ' + GameElement.TXT_IS_NOT_CORRECT + '.', txt_n_min_max_players)
        else:
            version = [version for version in self.versions if sys.argv[2] == version.name][0]  # type: Version
        # Read the colors of the players from the XML file.
        self.color_players = list()
        for color_player_name_tag in xml_tree_root.findall('color_players/color_player'):
            self.color_players.append(ColorPlayer(color_player_name_tag.text))
        # Check the players (colors and ai names, 1! human).
        n_humans = 0  # type: int
        color_player_names = [color_player.name for color_player in self.color_players]  # type: List[str]
        for arg in [sys.argv[i_arg] for i_arg in range(3, n_args)]:
            list_arg = arg.split('=')  # type: List[str]
            if len(list_arg) == 1:  # human: <color>
                if list_arg[0] not in color_player_names:
                    self.usage('The color ' + list_arg[0] + ' for the human of the argument ' + arg + ' ' +
                               GameElement.TXT_IS_NOT_CORRECT + '.', txt_n_min_max_players)
                else:
                    n_humans += 1
                    color_player_names.remove(list_arg[0])
            elif len(list_arg) == 2:  # ai: <color=ai_name>
                if list_arg[0] not in color_player_names:
                    self.usage('The color ' + list_arg[0] + ' for an AI of the argument ' + arg + ' ' +
                               GameElement.TXT_IS_NOT_CORRECT + '.', txt_n_min_max_players)
                elif list_arg[1] not in AIPlayer.ai_names():
                    self.usage('The name ' + list_arg[1] + ' of an AI of the argument ' + arg + ' ' +
                               GameElement.TXT_IS_NOT_CORRECT + '.', txt_n_min_max_players)
                else:
                    color_player_names.remove(list_arg[0])
            else:
                self.usage('The argument ' + arg + ' ' + GameElement.TXT_IS_NOT_CORRECT + '.', txt_n_min_max_players)
        if n_humans != 1:
            self.usage('The number of human players ' + str(n_humans) + ' ' + GameElement.TXT_IS_NOT_CORRECT + '.',
                       txt_n_min_max_players)
        # Read all the remaining data from the XML file: name of the game.
        self.game_name = xml_tree_root.find('game_name').text
        # Read all the remaining data from the XML file: 3 parts of the castle (sorted by number of PP decreasing).
        n_prestige_pts_castle_parts = list()  # type: List[Tuple(int, Castle)]
        for castle_part_tag in xml_tree_root.findall('setup/setup_castle/*'):
            front_color_castle = castle_part_tag.find('front_color').text  # type: str
            name_castle = castle_part_tag.find('name').text  # type: str
            n_castle_tokens = [None] * self.n_min_players  # type: List[int]
            for n_players in range(self.n_min_players, self.n_max_players + 1):
                n_castle_tokens.append(int(
                    castle_part_tag.find('n_castle_tokens/n_castle_tokens_for_' + str(n_players) + '_players').text))
            n_prestige_pts_castle = int(castle_part_tag.find('n_prestige_pts').text)  # type: int
            n_prestige_pts_castle_parts.append((n_prestige_pts_castle,
                                                Castle(front_color_castle, name_castle, n_castle_tokens,
                                                       n_prestige_pts_castle)))
        self.castle = [castle_part
                       for n_prestige_pts, castle_part in sorted(n_prestige_pts_castle_parts, reverse=True)]
        # Read all the remaining data from the XML file: money.
        self.money = Money(xml_tree_root.find('money/name').text, int(xml_tree_root.find('money/number').text))
        # Read all the remaining data from the XML file: resources.
        self.resources = list()
        for resource_tag in xml_tree_root.findall('resources/resource'):
            self.resources.append(Resource(resource_tag.find('name').text, int(resource_tag.find('number').text)))
        # Read all the remaining data from the XML file: phases.
        self.phases = [None]
        specific_phase_tag = None  # type: xml.etree.ElementTree.Element
        for phase_tag in xml_tree_root.findall('phases/phase'):
            belongs_to_beginner_version_phase = phase_tag.find(
                'belongs_to_beginner_version').text == 'True'  # type: bool
            numero_phase = int(phase_tag.find('numero').text)  # type: int
            if numero_phase != len(self.phases):
                self.usage('The numeros of the phases (see ' + str(numero_phase) + ') are not ordered.')
            name_phase = phase_tag.find('name').text  # type: str
            if numero_phase == 1:
                specific_phase_tag = xml_tree_root.find('phase_income/gain')
                self.phases.append(IncomePhase(belongs_to_beginner_version_phase, numero_phase, name_phase,
                                               int(specific_phase_tag.find('n_deniers').text),
                                               int(specific_phase_tag.find('n_deniers_per_residence').text),
                                               int(specific_phase_tag.find('n_deniers_if_hotel').text)))
            elif numero_phase == 2:
                specific_phase_tag = xml_tree_root.find('phase_actions')
                self.phases.append(ActionsPhase(belongs_to_beginner_version_phase, numero_phase, name_phase,
                                                int(specific_phase_tag.find('cost/n_deniers_to_take_a_card').text),
                                                int(specific_phase_tag.find(
                                                    'cost/n_deniers_to_discard_all_cards').text),
                                                int(specific_phase_tag.find(
                                                    'cost/n_deniers_to_place_a_worker').text),
                                                int(specific_phase_tag.find('cost/n_workers').text),
                                                int(specific_phase_tag.find(
                                                    'gain/n_deniers_for_first_player_passing').text)))
            elif numero_phase == 3:
                specific_phase_tag = xml_tree_root.find('phase_provost_movements')
                self.phases.append(ProvostMovementPhase(belongs_to_beginner_version_phase, numero_phase, name_phase,
                                                        int(specific_phase_tag.find(
                                                            'n_turns_to_move_provost').text),
                                                        int(specific_phase_tag.find(
                                                            'n_deniers_per_a_provost_movement').text),
                                                        int(specific_phase_tag.find(
                                                            'n_max_provost_movements_per_player').text)))
            elif numero_phase == 4:
                self.phases.append(
                    EffectsBuildingsPhase(belongs_to_beginner_version_phase, numero_phase, name_phase))
            elif numero_phase == 5:
                specific_phase_tag = xml_tree_root.find('phase_castle')
                self.phases.append(CastlePhase(belongs_to_beginner_version_phase, numero_phase, name_phase,
                                               int(specific_phase_tag.find(
                                                   'gain/n_gold_cubes_for_player_offered_most_batches').text),
                                               int(specific_phase_tag.find(
                                                   'no_gain/n_prestige_pt_tokens_to_remove').text),
                                               GameElement.get_resources_from_XML_tag(specific_phase_tag, 'cost')))
            elif numero_phase == 6:
                specific_phase_tag = xml_tree_root.find('phase_end_turn')
                self.phases.append(EndTurnPhase(belongs_to_beginner_version_phase, numero_phase, name_phase,
                                                int(specific_phase_tag.find('n_provost_advances').text)))
            else:
                self.usage('The numero ' + str(numero_phase) + ' of a phase ' + GameElement.TXT_IS_NOT_CORRECT + '.')
        # Prepare the reading of all the buildings from the XML file.
        Building.game_element = self
        self.buildings = list()
        can_be_a_prestige_building = None  # type: bool
        allows_to_place_a_worker = None  # type: bool
        front_color = None  # type: str
        belongs_to_beginner_version = None  # type: bool
        name = None  # type: str
        n_prestige_pts = None  # type: int
        resource_costs = None  # type: Dict[Optional[Resource], int]
        primary_effect = None  # type: Effect
        secondary_effect = None  # type: Effect
        can_be_a_residential_building = None  # type: bool
        resource = None  # type: Resource
        # Read all the remaining data from the XML file: prestige buildings.
        prestige_buildings_tag = xml_tree_root.find(
            'buildings/prestige_buildings')  # type: xml.etree.ElementTree.Element
        can_be_a_prestige_building = prestige_buildings_tag.find('can_be_a_prestige_building').text == 'True'
        allows_to_place_a_worker = prestige_buildings_tag.find('allows_to_place_a_worker').text == 'True'
        front_color = prestige_buildings_tag.find('front_color').text
        for prestige_building_tag in prestige_buildings_tag.findall('prestige_building'):
            belongs_to_beginner_version = prestige_building_tag.find('belongs_to_beginner_version').text == 'True'
            name = prestige_building_tag.find('name').text
            n_prestige_pts = int(prestige_building_tag.find('n_prestige_pts').text)
            resource_costs = GameElement.get_resources_from_XML_tag(prestige_building_tag, 'cost')
            if name == 'Hotel':
                self.buildings.append(
                    HotelPrestigeBuilding(belongs_to_beginner_version, can_be_a_prestige_building,
                                          allows_to_place_a_worker, front_color, name, n_prestige_pts,
                                          GameElement.get_effect_from_XML_tag(prestige_building_tag, self.phases),
                                          resource_costs, None))
            else:
                self.buildings.append(
                    PrestigeBuilding(belongs_to_beginner_version, can_be_a_prestige_building,
                                     allows_to_place_a_worker, front_color, name, n_prestige_pts, None, resource_costs,
                                     None))
        # Read all the remaining data from the XML file: neutral building.
        neutral_buildings_tag = xml_tree_root.find(
            'buildings/neutral_buildings')  # type: xml.etree.ElementTree.Element
        belongs_to_beginner_version = neutral_buildings_tag.find('belongs_to_beginner_version').text == 'True'
        can_be_a_prestige_building = neutral_buildings_tag.find('can_be_a_prestige_building').text == 'True'
        allows_to_place_a_worker = neutral_buildings_tag.find('allows_to_place_a_worker').text == 'True'
        front_color = neutral_buildings_tag.find('front_color').text
        n_prestige_pts = 0
        for neutral_building_tag in neutral_buildings_tag.findall('neutral_building'):
            name = neutral_building_tag.find('name').text
            if name == 'Peddler':
                neutral_building = PeddlerNeutralBuilding(belongs_to_beginner_version, can_be_a_prestige_building,
                                                          allows_to_place_a_worker, front_color, name,
                                                          n_prestige_pts,
                                                          GameElement.get_effect_from_XML_tag(neutral_building_tag,
                                                                                              self.phases), None)
            else:
                neutral_building = NeutralBuilding(belongs_to_beginner_version, can_be_a_prestige_building,
                                                   allows_to_place_a_worker, front_color, name, n_prestige_pts,
                                                   GameElement.get_effect_gain_from_XML_tag(neutral_building_tag,
                                                                                            self.phases), None)
            self.buildings.append(neutral_building)
        # Read all the remaining data from the XML file: background player building.
        background_player_building_tag = xml_tree_root.find(
            'buildings/background_player_building')  # type: xml.etree.ElementTree.Element
        belongs_to_beginner_version = background_player_building_tag.find(
            'belongs_to_beginner_version').text == 'True'
        can_be_a_prestige_building = background_player_building_tag.find(
            'can_be_a_prestige_building').text == 'True'
        allows_to_place_a_worker = background_player_building_tag.find('allows_to_place_a_worker').text == 'True'
        front_color = background_player_building_tag.find('front_color').text
        name = background_player_building_tag.find('name').text
        resource_costs = GameElement.get_resources_from_XML_tag(background_player_building_tag, 'cost')
        n_prestige_pts = int(background_player_building_tag.find('n_prestige_pts').text)
        primary_effect = GameElement.get_effect_from_XML_tag(background_player_building_tag, self.phases)
        for color_player in self.color_players:
            background_player_building = BackgroundPlayerBuilding(belongs_to_beginner_version,
                                                                  can_be_a_prestige_building, allows_to_place_a_worker,
                                                                  front_color, name, n_prestige_pts, primary_effect,
                                                                  resource_costs, color_player)
            self.buildings.append(background_player_building)
            color_player.setup(background_player_building)
        # Read all the remaining data from the XML file: player buildings.
        player_buildings_tag = xml_tree_root.find(
            'buildings/player_buildings')  # type: xml.etree.ElementTree.Element
        can_be_a_prestige_building = player_buildings_tag.find('can_be_a_prestige_building').text == 'True'
        allows_to_place_a_worker = player_buildings_tag.find('allows_to_place_a_worker').text == 'True'
        for player_building_tag in player_buildings_tag.findall('player_building'):
            belongs_to_beginner_version = player_building_tag.find('belongs_to_beginner_version').text == 'True'
            can_be_a_residential_building = player_building_tag.find('can_be_a_residential_building').text == 'True'
            front_color = player_building_tag.find('front_color').text
            name = player_building_tag.find('name').text
            n_prestige_pts = int(player_building_tag.find('n_prestige_pts').text)
            if player_building_tag.find('construction') is not None:
                resource_costs = GameElement.get_resources_from_XML_tag(player_building_tag, 'cost')
                primary_effect = GameElement.get_any_effect_gain_from_XML_tag(player_building_tag, 'primary_effect')
                secondary_effect = GameElement.get_any_effect_gain_from_XML_tag(player_building_tag,
                                                                                'secondary_effect')
                n_cubes_into_area = [None] * self.n_min_players  # type: List[int]
                for construction_tag in player_building_tag.findall('construction/*'):
                    construction_tag_split = construction_tag.tag.split(
                        '_')  # type: List[str] # E.g. 'n_food_cubes_into_area' -> ['n', 'food', 'cubes', 'into', 'area'].
                    if len(construction_tag_split) > 1:
                        resource = Resource.get_resource(construction_tag_split[1])
                        for n_players in range(self.n_min_players, self.n_max_players + 1):
                            n_cubes_into_area.append(int(construction_tag.find(
                                construction_tag.tag + '_for_' + str(n_players) + '_players').text))
                for color_player in self.color_players:
                    small_production_player_building = SmallProductionPlayerBuilding(
                        belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                        front_color, name, n_prestige_pts, primary_effect, resource_costs,
                        can_be_a_residential_building, secondary_effect, color_player, resource,
                        n_cubes_into_area)  # type: SmallProductionPlayerBuilding
                    self.buildings.append(small_production_player_building)
            elif name.startswith('Large '):
                resource_costs = GameElement.get_resources_from_XML_tag(player_building_tag, 'cost')
                primary_effect = GameElement.get_any_effect_gain_from_XML_tag(player_building_tag, 'primary_effect')
                secondary_effect = GameElement.get_any_effect_gain_from_XML_tag(player_building_tag,
                                                                                'secondary_effect')
                resource = Resource.get_resource(player_building_tag.find(
                    'primary_effect/gain/').tag)  # We assume the resource is the same for the gain of the primary and secondary effects.
                for color_player in self.color_players:
                    large_production_player_building = LargeProductionPlayerBuilding(
                        belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                        front_color, name, n_prestige_pts, primary_effect, resource_costs,
                        can_be_a_residential_building, secondary_effect, color_player,
                        resource)  # type: LargeProductionPlayerBuilding
                    self.buildings.append(large_production_player_building)
            elif name == 'Lawyer':
                resource_costs = GameElement.get_resources_from_XML_tag(player_building_tag, 'cost')
                primary_effect = GameElement.get_any_effect_from_XML_tag(player_building_tag, 'primary_effect')
                secondary_effect = GameElement.get_one_money_effect_gain_from_XML_tag(player_building_tag,
                                                                                      'secondary_effect')
                n_residence_to_construct = 1  # type: int
                for color_player in self.color_players:
                    lawyer_player_building = LawyerPlayerBuilding(
                        belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                        front_color, name, n_prestige_pts, primary_effect, resource_costs,
                        can_be_a_residential_building, secondary_effect, color_player,
                        n_residence_to_construct)  # type: LawyerPlayerBuilding
                    self.buildings.append(lawyer_player_building)
            else:
                resource_costs = GameElement.get_resources_from_XML_tag(player_building_tag, 'cost')
                primary_effect = GameElement.get_any_effect_from_XML_tag(player_building_tag, 'primary_effect')
                secondary_effect = GameElement.get_any_effect_from_XML_tag(player_building_tag, 'secondary_effect')
                for color_player in self.color_players:
                    if name == 'Peddler':
                        player_building = PeddlerPlayerBuilding(
                            belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                            front_color, name, n_prestige_pts, primary_effect, resource_costs,
                            can_be_a_residential_building, secondary_effect,
                            color_player)  # type: PeddlerPlayerBuilding
                    elif name == 'Market':
                        secondary_effect = GameElement.get_one_money_effect_gain_from_XML_tag(player_building_tag,
                                                                                              'secondary_effect')
                        player_building = MarketPlayerBuilding(
                            belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                            front_color, name, n_prestige_pts, primary_effect, resource_costs,
                            can_be_a_residential_building, secondary_effect,
                            color_player)  # type: MarketPlayerBuilding
                    elif name == 'Gold Mine':
                        primary_effect = GameElement.get_any_effect_gain_from_XML_tag(player_building_tag,
                                                                                      'primary_effect')
                        player_building = GoldMinePlayerBuilding(
                            belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                            front_color, name, n_prestige_pts, primary_effect, resource_costs,
                            can_be_a_residential_building, secondary_effect,
                            color_player)  # type: GoldMinePlayerBuilding
                    elif name == 'Bank':
                        player_building = BankPlayerBuilding(
                            belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                            front_color, name, n_prestige_pts, primary_effect, resource_costs,
                            can_be_a_residential_building, secondary_effect,
                            color_player)  # type: BankPlayerBuilding
                    elif name == 'Church':
                        player_building = ChurchPlayerBuilding(
                            belongs_to_beginner_version, can_be_a_prestige_building, allows_to_place_a_worker,
                            front_color, name, n_prestige_pts, primary_effect, resource_costs,
                            can_be_a_residential_building, secondary_effect,
                            color_player)  # type: ChurchPlayerBuilding
                    else:
                        GameElement.usage('The player building ' + name + ' ' + GameElement.TXT_IS_NOT_CORRECT + '.',
                                          txt_n_min_max_players)
                    self.buildings.append(player_building)
        # Read all the remaining data from the XML file: road setup.
        setup_road_tag = xml_tree_root.find('setup/setup_road')  # type: xml.etree.ElementTree.Element
        self.last_neutral_building = NeutralBuilding.get_neutral_building(
            setup_road_tag.find('last_neutral_building').text)
        self.place_provost = NeutralBuilding.get_neutral_building(setup_road_tag.find('place_provost').text)
        self.n_all_except_last_neutral_buildings = [None] * self.n_min_players
        for n_players in range(self.n_min_players, self.n_max_players + 1):
            self.n_all_except_last_neutral_buildings.append(int(setup_road_tag.find(
                'n_all_except_last_neutral_buildings/n_all_except_last_neutral_buildings_for_' +
                str(n_players) + '_players').text))
        # Read all the remaining data from the XML file: players.
        players = list()  # type: List[Player]
        setup_player_tag = xml_tree_root.find('setup/setup_player')  # type: xml.etree.ElementTree.Element
        self.n_cards_in_hand = int(setup_player_tag.find('n_cards_in_hand').text)
        self.n_possibilities_to_discard_cards = int(setup_player_tag.find('n_possibilities_to_discard_cards').text)
        Player.n_workers = int(setup_player_tag.find('n_workers').text)
        Player.money_resources = {}
        Player.money_resources[Money.money] = int(setup_player_tag.find('n_deniers').text)
        for resource_name, resource in Resource.resources.items():
            Player.money_resources[resource] = int(setup_player_tag.find('n_' + resource_name + '_cubes').text)
        Player.n_prestige_pts = int(setup_player_tag.find('n_prestige_pts').text)
        for list_arg in [sys.argv[i_arg].split('=') for i_arg in range(3, n_args)]:
            color_player = ColorPlayer.colors_players[list_arg[0]]  # type: ColorPlayer
            if len(list_arg) == 1:
                players.append(HumanPlayer(color_player))
            else:
                if list_arg[1] == BasicAIPlayer.ai_name:
                    players.append(BasicAIPlayer(color_player))
                else:
                    players.append(AdvancedAIPlayer(color_player))
        # End of the initialization of the elements of the game obtained from the XML file.
        print('Initialization of the elements of "' + self.game_name + '": ' +
              str(len(self.versions)) + ' versions, ' +
              str(len(self.color_players)) + ' colors of players, ' +
              str(len(self.castle)) + ' parts of the castle, ' +
              ('no money, ' if Money.money is None else 'one money, ') +
              str(len(self.resources)) + ' resources, ' +
              str(len(self.phases)) + ' phases, ' +
              str(len(self.buildings)) + ' buildings.')
        # Initialization of the game.
        self.game = Game(self, version, players)

    @staticmethod
    def usage(error_msg: str, txt_n_min_max_players: str = '?') -> None:
        """Usage of the command."""
        print(error_msg)
        print('Usage: python ' + sys.argv[0] + ' <XML_file> {Beginner|Standard} <color>[=<ai_name>]^' +
              txt_n_min_max_players)
        print(
            'Example of beginner version and 4 players (human (2nd pos., green color) faces 2 basic and 1 advanced AIs):')
        print('\tpython ' + sys.argv[0] +
              ' game_elements-CaylusMagnaCarta.xml Beginner red=Basic green orange=Advanced blue=Basic')
        exit(1)

    @staticmethod
    def get_resource_name_from_XML_tag(tag) -> str:
        """Get the name of a resource (food, wood, stone or gold) from the text of a tag in the XML file."""
        return tag.tag.split('_')[1]  # Z.g. 'n_food_cubes' -> 'food'.

    @staticmethod
    def get_resources_from_XML_tag(tag, sub_tag):  # -> Dict[Optional[Resource], int]
        """Get the resources from all subtags (e.g. cost, gain) of a tag in the XML file."""
        resources = {}  # type: Dict[Optional[Resource], int]
        for resource_tag in tag.findall(sub_tag + '/*'):
            if resource_tag.tag == 'CHOICES':
                # None if for the number of "white cubes" stand for cubes of any kind (including gold).
                # We search only one resource (gold can be replaced by any other resource).
                resources[None] = int(resource_tag.find('CHOICE/n_gold_cubes').text)
            else:
                resources[Resource.resources[GameElement.get_resource_name_from_XML_tag(resource_tag)]] = int(
                    resource_tag.text)
        return resources

    @staticmethod
    def get_effect_from_XML_tag(tag, phases) -> Effect:
        """Get the effect (text and phase numero) from a tag in the XML file."""
        # WARNING: get also effect/cost/... and effect/gain/...
        return Effect(tag.find('effect/text').text, phases[1 + int(tag.find('effect/phase_numero').text)])

    @staticmethod
    def get_effect_gain_from_XML_tag(tag, phases) -> Effect:
        """Get the effect (text and phase numero) and the gain (money or one resource) from a tag in the XML file."""
        gain_tag = tag.find('effect/gain/')  # type: xml.etree.ElementTree.Element
        money_resource_gain = None  # type: Tuple[MoneyResource, int] # Money or resource gain.
        if gain_tag.tag == 'n_deniers':
            money_resource_gain = (Money.money, int(gain_tag.text))
        else:
            money_resource_gain = (Resource.resources[GameElement.get_resource_name_from_XML_tag(gain_tag)],
                                   int(gain_tag.text))
        return Effect(tag.find('effect/text').text, phases[1 + int(tag.find('effect/phase_numero').text)], None,
                      money_resource_gain)

    @staticmethod
    def get_any_effect_from_XML_tag(tag, effect_name: str) -> Effect:
        """Get the primary or secondary effect (text) from a tag in the XML file."""
        # WARNING: get also, from effect_name, /cost/... and /gain/... and /gain/CHOICES/...
        return Effect(tag.find(effect_name + '/text').text, None)

    @staticmethod
    def get_one_money_effect_gain_from_XML_tag(tag, effect_name: str) -> Effect:
        """Get the effect (text) and the gain (one money) from a tag in the XML file."""
        return Effect(tag.find(effect_name + '/text').text, None, None,
                      (Money.money, int(tag.find(effect_name + '/gain/n_deniers').text)))

    @staticmethod
    def get_any_effect_gain_from_XML_tag(tag, effect_name: str) -> Effect:
        """Get the primary or secondary effect (text) and the gain (one resource) from a tag in the XML file."""
        gain_tag = GameElement.get_one_resource_tag_from_XML_tag(tag,
                                                                 effect_name + '/gain')  # type: xml.etree.ElementTree.Element
        return Effect(tag.find(effect_name + '/text').text, None, None,
                      (Resource.resources[GameElement.get_resource_name_from_XML_tag(gain_tag)], int(gain_tag.text)))

    @staticmethod
    def get_one_resource_tag_from_XML_tag(tag, sub_tag_name: str):  # -> xml.etree.ElementTree.Element
        """Get (only) one resource tag from a tag and the sub tag name in the XML file."""
        # WARNING: code to find directly something like 'n_'<resource>'_cubes' or 'n_'<resource>'_cubes_into_area'.
        resource_tag = None  # type: xml.etree.ElementTree.Element
        for sub_tag in tag.findall(sub_tag_name + '/*'):  # We must avoid other tags.
            if resource_tag is None:
                sub_tag_split = sub_tag.tag.split(
                    '_')  # type: List[str] # E.g. 'n_food_cubes' -> ['n', 'food', 'cubes'].
                if len(sub_tag_split) > 1:
                    resource_tag = sub_tag
        return resource_tag


if __name__ == "__main__":
    print('Hello.')
    game = GameElement().game
    game.setup()
    game.play()
    print('Bye.')
