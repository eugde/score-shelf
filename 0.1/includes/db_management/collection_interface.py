import sqlite3

from misc import constants, data_linking, helper_functions
import db_interface


class CollectionHandler:
    def __init__(self, name, db, linker):

        self.name = name
        self.db = db
        self.groups = []
        self.linker = linker

        self.id = None
        self.update_collection_id()
        self.groups = {}
        self.update_groups()

    def update_collection_id(self):
        col_id = self.db.fetch_table("collections", columns=["collection_id"], condition=[("collection_name = ",self.name),])
        if col_id:
            self.id = col_id[0][0]
        else:
            self.id = self.db.insert_into_table("collections", {"collection_name": self.name})

    def get_groupmembers(self, group_table, col_name, id_name = None):
        """
        Returns all the unique members of a group.
        To be used e.g. to get a list of criteria to sort data by.

        @param group_table: The name of the table to get the data from.
        @param col_name: The column inside the table where the data is stored.
        @param id_name: The column where the reference-id is stored inside 'tracks'.
        """

        col_ids = []

        if not id_name:
            id_name = col_name.split("name")[0]+"id"
        id_location = constants.TRACK_INSERT_COLS.index(id_name) + 1

        entries = self.get_all_entries()
        if entries:
            for track in entries:
                col_ids.append(track.data[id_location][1])

        #Remove duplicates
        col_ids = list(set(col_ids))


        if len(col_ids) > 1:
            sql = "SELECT {} FROM {} WHERE {} IN {}".format(col_name, group_table, id_name, tuple(col_ids))
        elif len(col_ids) == 1:
            sql = "SELECT {} FROM {} WHERE {} = '{}'".format(col_name, group_table, id_name, col_ids[0])
        else:
            return False

        data = []

        with self.db.db_connection:
            print(sql)
            self.db.cursor.execute(sql)
            result = self.db.cursor.fetchall()
            for row in result:
                data.append(row[0])
        data.sort()
        return data

    def update_groups(self):
        interpreters = self.get_groupmembers("interpreters", "interpreter_name")
        composers = self.get_groupmembers("composers", "composer_name")
        genres = self.get_groupmembers("genres", "genre_name")

        self.groups["Interpreten"] = interpreters
        self.groups["Komponisten"] = composers
        self.groups["Genres"] = genres

    def get_all_entries(self):
        """
        Fetches all tracks from the 'tracks' table which have a connection with the collection.
        """

        sql_fetch_tids = "SELECT track_id FROM collections_tracks WHERE collection_id = {}".format(self.id)
        tids = []
        try:
            with self.db.db_connection:
                self.db.cursor.execute(sql_fetch_tids)
                for line in self.db.cursor.fetchall():
                    tids.append(line[0])

            sql_fetch_tracks = "SELECT {} FROM {} WHERE tracks.track_id IN ".format(
                                                                                ", ".join(constants.ENTRY_COLS_SORTED),
                                                                                constants.JOIN_COLS)
            sql_fetch_tracks += helper_functions.create_placeholders(len(tids))
            results = []
            with self.db.db_connection:
                self.db.cursor.execute(sql_fetch_tracks, tuple(tids))
                for entry in self.db.cursor.fetchall():
                    results.append(db_interface.Entry(entry))
            return results
        except sqlite3.OperationalError as e:
            print(e.args[0])
            return None

    def add_entry(self, entry):
        """
        Adds an entry to the collection.

        @entry: Member of the 'Entry'-class. Obtainable e.g. via TrackDbHandler.get_entries()
        """

        track_id = entry.get_track_id()
        sql_check_dupl = "SELECT * FROM collections_tracks WHERE track_id = ? AND collection_id = ?"
        with self.db.db_connection:
            self.db.cursor.execute(sql_check_dupl, (track_id, self.id))
            if not self.db.cursor.fetchall():
                sql = "INSERT INTO collections_tracks VALUES (?, ?)"
                self.db.cursor.execute(sql, (track_id, self.id))
                self.update_groups()
                return True
            else:
                return False

    def delete_entry(self, entry = None, track_id = None):

        if entry:
            track_id = entry.get_track_id()
        print(track_id)
        sql = "DELETE FROM collections_tracks WHERE track_id = ? AND collection_id = ?"
        with self.db.db_connection:
            self.db.cursor.execute(sql, (track_id, self.id))
            self.update_groups()



if __name__ == "__main__":
    test = CollectionHandler("test", db_interface.TrackDbHandler("data/test2.db"), data_linking.LinkingHandler())

    print(test.groups)
    print(test.id)
    test.db.output_table("collections_tracks")
    for entry in (test.get_all_entries()):
        print(entry)




