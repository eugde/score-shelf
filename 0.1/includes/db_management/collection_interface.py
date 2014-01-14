from misc import constants, data_linking
import db_interface


class CollectionHandler():
    def __init__(self, name, db, linker):
        self.name = name
        self.db = db
        self.groups = []

    def get_groupmembers(self, group_table, col_name):
        """
        Returns all the unique members of a group.
        To be used e.g. to get a list of criteria to sort data by.

        @param group_table: The name of the table to get the data from.
        @param col_name: The column inside the table where the data is stored.
        """

        sql = "SELECT {} FROM {}".format(col_name, group_table)
        with self.db.db_connection:
            print(sql)
            self.db.cursor.execute(sql)
            data = self.db.cursor.fetchall()
        print(data)

if __name__ == "__main__":
    test = CollectionHandler("test", db_interface.TrackDbHandler("data/test2.db"), data_linking.LinkingHandler())
    test.get_groupmembers("composers", "composer_name")


