#!/usr/bin/python


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


#Metaclass verifiant l'existance d' une instance
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Money(MoneyResource,metaclass=Singleton):
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
    def get_wild_resource():
        return list(filter(lambda res : res.is_wild(), Resource.resources.values()))[0]
        

