from ..APIHelper import APIHelper
from .Steam import Steam
from .GOG import GOG
from .Epic import Epic
import logging

logger = logging.getLogger(__name__)


class StoreHandler(APIHelper):
    def __init__(self):
        self.steam = Steam()
        self.gog = GOG()
        self.epic = Epic()
