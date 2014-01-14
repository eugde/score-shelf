from misc import constants, data_linking
import db_interface


class CollectionHandler():
    def __init__(self, name, db, linker):
        self.name = name
        self.db = db
        self.groups = []
        self.linker = linker
        self.groups = {}
        self.update_groups()

    def get_groupmembers(self, group_table, col_name):
        """
        Returns all the unique members of a group.
        To be used e.g. to get a list of criteria to sort data by.

        @param group_name: The name of the group which can be used as root for a Tree-View.
        @param group_table: The name of the table to get the data from.
        @param col_name: The column inside the table where the data is stored.
        """

        sql = "SELECT {} FROM {}".format(col_name, group_table)
        data = []

        with self.db.db_connection:
            self.db.cursor.execute(sql)
            result = self.db.cursor.fetchall()
            for row in result:
                data.append(row[0])
        return data

    def update_groups(self):
        interpreters = self.get_groupmembers("interpreters", "interpreter_name")
        composers = self.get_groupmembers("composers", "composer_name")
        genres = self.get_groupmembers("genres", "genre_name")

        self.groups["Interpreten"] = interpreters
        self.groups["Komponisten"] = composers
        self.groups["Genres"] = genres



if __name__ == "__main__":
    test = CollectionHandler("test", db_interface.TrackDbHandler("data/test2.db"), data_linking.LinkingHandler())
    print(test.groups)


