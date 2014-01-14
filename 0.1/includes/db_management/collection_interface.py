from misc import constants, data_linking
import db_interface


class CollectionHandler():
    def __init__(self, name, linker):
        self.name = name
