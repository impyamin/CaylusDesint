#!/usr/bin/python

import abc
import collections
import random
import itertools


from game.utils import indent
from game.utils import TXT_SEPARATOR

from game.utils import Location
from phases import Phase
from phases import CastlePhase
from moneyres import Resource
from moneyres import MoneyResource
from moneyres import Money




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


