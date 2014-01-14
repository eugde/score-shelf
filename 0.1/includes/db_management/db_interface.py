import sqlite3
import os, sys
import random

import constants
from misc.myExceptions import MissingTableError, InvalidColumnError
from misc.helper_functions import contains, dict_factory


class DbHandler:
    """
    This class handles all database-related operations in the program.
    """

    def __init__(self, db_name):
        """
        Creates a new DbHandler-Object to a new or existing database. A cursor-object is also initiated.

        @param db_name: The name of the database, if an invalid name is given a random number will be generated as name.
        """

        self.db_name = db_name
        #self.conversion_list = {"int": "INTEGER", "None": "NULL", "float":"REAL", "bytes": "TEXT", "str": "TEXT"}

        try:
            self.db_connection = sqlite3.connect(self.db_name)
        except TypeError:
            self.db_name = str(random.randint(99999, 999999)) + ".db"
            self.db_connection = sqlite3.connect(self.db_name)
        except sqlite3.Error as e:
            print("Error: "+e.args[0])

        self.cursor = self.db_connection.cursor()
        self.tables = []
        self.db_information = {}
        self.update_db_description()

    #Table-Management

    def __del__(self):
        self.db_connection.commit()
        self.db_connection.close()

    def create_table(self, table_name, cols):
        """
        Creates a new table with the given columns.

        @param table_name: Name of the new table.
        Note: If this is the name of an existing table, it will not override the old table.

        @param cols: The columns of the new table.
        Must be a list containing tuples of names and corresponding SQL-types such as ("id", "INTEGER")
        """

        sql = "CREATE TABLE IF NOT EXISTS {} (".format(table_name)

        for entry in cols:
            sql += "{} {},".format(entry[0],entry[1])

        sql = str(sql.rsplit(",", 1)[0])
        sql += " )"

        #print(sql)

        with self.db_connection:
            self.cursor.execute(sql)
        self.update_db_description()

    def alter_table(self, table_name, cols):
        """
        Takes an existing table and alters its columns.
        NOTE: Pre-Existing Columns not included in cols will be deleted!

        @param table_name: A string containing the name of the table to be altered.
        @param cols: A list of tuples containing the columns for the new table.
        """

        self.update_db_description()
        temp_table_name = table_name+"_temp"
        try:
            if table_name in self.db_information:
                sql_alter_temp_statement = "ALTER TABLE {} RENAME TO {}".format(table_name,temp_table_name)
                with self.db_connection:
                    self.cursor.execute(sql_alter_temp_statement)
                self.update_db_description()
            else:
                raise MissingTableError(table_name, self.db_name)
        except MissingTableError as e:
            print(e.message)
            sys.exit(0)

        self.create_table(table_name, cols)
        print(self.db_information)

        old_columns = self.fetch_table_description(temp_table_name)
        new_columns = [x[0] for x in cols]
        columns_to_copy = [x for x in new_columns if x in old_columns]
        print("COPY COLUMNS ",columns_to_copy)

        self.copy_data_into_table(temp_table_name, table_name, columns_to_copy)
        self.drop_table(temp_table_name)
        self.update_db_description()

    def copy_data_into_table(self, source_table, target_table, columns):
        """
        This function copies the data out of all the specified columns from one table to another.

        @param source_table: The table where the data is copied from.
        @param target_table: The table where the data is copied into.
        @param columns: List of the column names to be copied.
        @return:
        """
        cols_source = self.fetch_table_description(source_table)
        cols_target = self.fetch_table_description(target_table)
        sql_cols = ", ".join(columns)
        try:
            if contains(columns, cols_source) and contains(columns, cols_target):
                #Positional arguments are used here to make the statement less confusing.
                sql = "INSERT INTO {0} ({1}) SELECT {2} FROM {3}".format(
                    target_table, sql_cols, sql_cols, source_table
                )

                with self.db_connection:
                    print(sql)
                    self.cursor.execute(sql)
            else:
                table_names = "{}, {}".format(source_table, target_table)
                columns = [self.fetch_table_description(source_table), self.fetch_table_description(target_table)]
                raise InvalidColumnError(table_names, sql_cols, columns)
        except InvalidColumnError as e:
            print(e.message)
            print(e.detail_info)

    def drop_table(self, table_name):
        """
        This function checks if a table exists in the database and drops it.

        @param table_name: A String containing the name of the table to be dropped.
        """

        sql = "DROP TABLE IF EXISTS {}".format(table_name)
        with self.db_connection:
            self.cursor.execute(sql)
            print("Table {} dropped!".format(table_name))
        self.update_db_description()

    #Data-Management

    def insert_into_table(self, table_name, *values):
        """
        Inserts a new row into a table.

        @param table_name: A string containing the name of the target table.
        @param values: One or several dictionaries containing column names and corresponding values.
        """

        table_columns = self.db_information[table_name]
        for entry in values:

            sql = "INSERT INTO {} (".format(table_name)
            temp_values = {}

            for col in entry:
                if col in table_columns:
                    temp_values[col] = entry[col]

            #Because dicts aren't in order this list is used to ensure the right values get entered
            #into the correct columns.
            ordered_keys = []
            for key in temp_values.keys():
                ordered_keys.append(key)
                sql += str(key)+","

            sql = str(sql.rsplit(",", 1)[0]) + ") VALUES ("

            for key in ordered_keys:
                sql += "'"+str(entry[key]) + "',"

            sql = str(sql.rsplit(",", 1)[0]) + ")"
            print(sql)

            if ordered_keys:
                with self.db_connection:
                    #print(sql)
                    self.cursor.execute(sql)
        return self.cursor.lastrowid

    def delete_from_table(self, table_name, col, value):
        """
        Deletes rows from the table 'table_name' where 'col' = 'value'

        @table_name: A string containing the name of the target table.
        @col: The column in the table containing the value for the WHERE-clause
        @value: The value the WHERE-clause checks against.
        """

        self.update_db_description()
        try:
            if table_name in self.db_information:
                sql = "DELETE FROM {} WHERE {} = ?".format(table_name, col)
                with self.db_connection:
                    self.cursor.execute(sql, (value,))
            else:
                raise MissingTableError(table_name, self.db_name)
        except MissingTableError as e:
            print(e.message)

    def update_table(self, table_name, values, condition, condition_operator = "AND"):
        """
        Updates rows in a table matching the condition.

        @param table_name: A string containing the name of the table to be updated.
        @param values: A list of one/more tuples containing the values which are to be updated. ((column: value),...)
        @param condition: A list of one/more tuples containing conditions for the WHERE-clause. ((column: value),...)

        """

        sql = "UPDATE {} SET ".format(table_name)
        sql_condition = "WHERE "
        sql_values = ""
        sql_parameters = []

        for value in values:
            sql_values += "{} = ?,".format(value[0])
            sql_parameters.append(value[1])

        sql += str(sql_values.rsplit(",", 1)[0]) + " "

        for con in condition:
            sql_condition += "{} ? {} ".format(con[0], condition_operator)
            sql_parameters.append(con[1])

        sql += str(sql_condition.rsplit(condition_operator, 1)[0]) + " "
        print(sql)
        print(sql_parameters)

        with self.db_connection:
            print(sql, sql_parameters)
            #print(tuple(sql_parameters))
            self.cursor.execute(sql,tuple(sql_parameters))

        self.update_db_description()


    #Database-Information

    def fetch_table_list(self):
        """
        Updates the list of existing tables inside the database.
        """

        with self.db_connection:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table';")
            del self.tables[:]
            for table_name in self.cursor.fetchall():
                self.tables.append(table_name[0])

    def fetch_table_description(self, table_name):
        """
        Fetches a list of all columns in one table.

        @param table_name: Name of the corresponding table.
        @return: A list containing the names of all the columns in the table.
        """

        with self.db_connection:
            column_list = []
            try:
                #String formatting is necessary because sqlite doesn't accept placeholders for table names!
                #This if-statement serves as alternative protection against sql-injection.
                #self.fetch_table_list()
                if table_name in self.tables:
                    with self.db_connection:
                        self.cursor.execute("SELECT * FROM {}".format(table_name))
                        for col in self.cursor.description:
                            column_list.append(col[0])
                else:
                    raise MissingTableError(table_name, self.db_name)
            except MissingTableError as e:
                print(e.message)
        return column_list

    def update_db_description(self):
        """
        Updates self.db_information, a dictionary containing all tables in the database and its columns.
        """

        self.fetch_table_list()
        for table in self.tables:
            self.db_information[table] = self.fetch_table_description(table)

    #Output

    def fetch_table(self, table_name, columns = [], condition = [], condition_operator = "AND", dict_output = False):
        """
        Returns a list of dictionaries containing the rows of the list which fulfill the condition.
        Per default it outputs all the columns as list.

        @param table_name: The name of the table to select the rows from.
        @param columns: The columns to be selected.
        @param condition: A list of tuples containing (column+condition)-value pairs for a WHERE-clause
        @param condition_operator: A standard logic operator to connect conditions.
        @param dict_output: If this is true, the function will return a dictionary instead of a list.
        @return: Either a list of a dictionary containing the data from the table.
        """

        self.update_db_description()
        try:
            if table_name in self.db_information:
                table_cols = self.fetch_table_description(table_name)
                if columns:
                    if contains(columns, table_cols):
                        columns = ", ".join(columns)
                        sql = "SELECT {} ".format(columns)
                    else:
                        raise InvalidColumnError(table_name,columns,table_cols)
                else:
                    sql = "SELECT * "
                sql += "FROM {} ".format(table_name)
                if condition:
                    sql_condition_placeholder = "WHERE "
                    values = []
                    for con in condition:
                        sql_condition_placeholder += "{} ? {} ".format(con[0], condition_operator)
                        values.append(con[1])

                    sql += sql_condition_placeholder.rsplit(condition_operator, 1)[0]
                    with self.db_connection:
                        if dict_output:
                            self.db_connection.row_factory = dict_factory
                            temp_cursor = self.db_connection.cursor()
                            temp_cursor.execute(sql, values)
                            data = temp_cursor.fetchall()
                        else:
                            self.cursor.execute(sql, values)
                            data = self.cursor.fetchall()
                            print(sql)
                else:
                    with self.db_connection:
                        if dict_output:
                            self.db_connection.row_factory = dict_factory
                            temp_cursor = self.db_connection.cursor()
                            temp_cursor.execute(sql)
                            data = temp_cursor.fetchall()
                        else:
                            self.cursor.execute(sql)
                            data = self.cursor.fetchall()

                return data
            else:
                raise MissingTableError(table_name, self.db_name)
        except MissingTableError as e:
            print(e.message)
        except InvalidColumnError as e:
            print(e.message)
            print(e.detail_info)


    def output_table(self, table_name):
        """
        Prints the table into the command line.

        @param table_name:
        """

        try:
            if table_name in self.db_information:
                print(table_name.upper())
                for col in self.fetch_table_description(table_name):
                    print(col,"|", end="\t")
                print("\n")

                sql = "SELECT * FROM {}".format(table_name)

                with self.db_connection:
                    #print(sql)
                    self.cursor.execute(sql)
                    for row in self.cursor.fetchall():
                        for col in row:
                            print (col,"|", end="\t")
                        print ("\n")
            else:
                raise MissingTableError(table_name, self.db_name)
        except MissingTableError as e:
            print(e.message)

    def get_foreign_key_value(self, table_name, key_column, value_column, value):
        sql = "SELECT {} FROM {} WHERE {} = ?".format(key_column, table_name, value_column)
        value_tup = (value,)
        with self.db_connection:
            self.cursor.execute(sql, value_tup)
            result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            result = self.insert_into_table(table_name, {value_column:value})
            return result


class TrackDbHandler(DbHandler):
    """
    This class exists to separate DB-operations specific to this programme and more general functions,
    which can be found in DbHandler.
    """
    def __init__(self, db_name, initialize = True):
        super(TrackDbHandler, self).__init__(db_name)

        self.foreign_keys = constants.FOREIGN_KEYS

        if initialize:
            self.create_table("composers", constants.COMPOSERS_COLS)
            self.create_table("interpreters", constants.INTERPRETERS_COLS)
            self.create_table("genres", constants.GENRES_COLS)
            self.create_table("collections", constants.COLLECTIONS_COLS)
            self.create_table("tracks", constants.TRACKS_COLS)
            self.create_table("collections_tracks", constants.COLLECTIONS_TRACKS_COLS)

    def get_entries(self, con_table = None, con_col = None, con_value = None):
        sql =   """
                SELECT
                    tracks.track_name,
                    tracks.year,
                    interpreters.interpreter_name,
                    composers.composer_name,
                    genres.genre_name,
                    tracks.media_location,
                    tracks.sheet_location,
                    tracks.thumbnail_location
                FROM
                    tracks
                    NATURAL LEFT JOIN interpreters
                    NATURAL LEFT JOIN composers
                    NATURAL LEFT JOIN genres
                """

        if con_table and con_col and con_value:
            sql += " WHERE {}.{} = ?".format(con_table, con_col)
            with self.db_connection:
                self.cursor.execute(sql, con_value)
                data = self.cursor.fetchall()
        else:
            with self.db_connection:
                self.cursor.execute(sql)
                data = self.cursor.fetchall()

        return data

    def input_entries(self, *args):
        """
        Handles the input of track-data into the correct tables.

        A parameter must have this form:
        arg = [str track_name, int year, str interpreter, str composer, str genre, str media, str sheet, str thumbnail]
        """

        sql =   """
                INSERT OR REPLACE INTO
                    tracks (track_name, year, interpreter_id, composer_id, genre_id,
                            media_location, sheet_location, thumbnail_location)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
        data = []
        for entry in args:
            #Fetching foreign key values
            if entry[2]:
                entry[2] = self.get_foreign_key_value("interpreters", "interpreter_id", "interpreter_name", entry[2])
            if entry[3]:
                entry[3] = self.get_foreign_key_value("composers", "composer_id", "composer_name", entry[3])
            if entry[4]:
                entry[4] = self.get_foreign_key_value("genres", "genre_id", "genre_name", entry[4])
            entry_line = tuple(entry)
            print("ENTRY LINE: ",entry_line)
            with self.db_connection:
                self.cursor.execute("""
                                    SELECT * FROM tracks WHERE  track_name = ? AND year = ? AND interpreter_id = ? AND
                                                                composer_id = ? AND genre_id = ?
                                    """, entry_line[0:5])
                if not self.cursor.fetchone():
                    #print(self.cursor.fetchall())
                    data.append(entry_line)
        with self.db_connection:
            if len(data) > 1:
                self.cursor.executemany(sql, data)
            elif len(data) == 1:
                print(data[0])
                self.cursor.execute(sql, data[0])

    def change_value(self, table_name, col, value, key_table = None, con = None):
        """
        Changes the value of one column.
        NOTE: If the column belongs to a foreign key the value of the referenced "_name"-column must be given as value.
        """

        try:
            if col in self.foreign_keys:
                if key_table:
                    value = self.get_foreign_key_value(key_table, col, self.foreign_keys[col], value)
                else:
                    raise sqlite3.IntegrityError
            self.update_table(table_name,[(col, value),], con)
        except sqlite3.IntegrityError as e:
            print(e.args[0])
            print("Value '{}' was not changed".format(value))

    def wipe_db(self):
        """
        Clears all the tables in the Database.
        """

        temp_tables = self.tables[:]
        for table in temp_tables:
            self.drop_table(table)

    def remove_duplicates(self):
        sql =   """
                DELETE FROM tracks WHERE track_id NOT IN
                (SELECT MAX(track_id) FROM tracks GROUP BY  track_name, year, interpreter_id, composer_id, genre_id,
                                                            media_location, sheet_location, thumbnail_location)
                """
        with self.db_connection:
            self.cursor.execute(sql)

if __name__ == "__test__":

    db = DbHandler("data/test.db")
    db.drop_table("test")
    db.create_table("test", [("id","INTEGER PRIMARY KEY"),("name","TEXT"), ("link_guitar","TEXT")])
    db.insert_into_table("test", {"name": "Hallo Welt"},{"name":"Tschüss Welt", "link_guitar": "asdf"},{"denkeygibtsned":"asdf"})

    #db.output_table("test")
    #db.update_table("test", [("name", "H4ll0 W3lt"), ("link_guitar", "Bass")], [("id =", 1),])
    #db.output_table("test")
    #db.alter_table("test", [("id","INTEGER PRIMARY KEY"),("name","TEXT"), ("link_guitar","TEXT"), ("link_bass", "TEXT")])
    db.output_table("test")

    print(db.tables)
    #table_data = db.fetch_table("test", ["id","name"], condition=[("id >", 2), ("id<",5)], dict_output=False)
    #print (table_data)
    print(db.get_foreign_key_value("test", "id", "link_guitar", "Bass"))
    print(db.get_foreign_key_value("test", "id", "link_guitar", "B4ss"))
    print(db.get_foreign_key_value("test", "id", "link_guitar", "Geige"))

    print(db.fetch_table("test"))

if __name__ == "__main__":
    #print(os.getcwd())
    db = TrackDbHandler(os.path.join(os.getcwd(), "data", "test2.db"), True)
    tables = db.tables[:]
    print(tables)
    #db.wipe_db()
    print(db.tables)
    #print(db.db_information)
    #db.input_entries(["Prälude 2", "1900", None, "Heitor Villa-Lobos", "Latein", None, None, None])
    #db.input_entries(["Prälude 1", "1910", "Andy McKee", "Heitor Villa-Lobos", "Latein", None, None, None])
    db.input_entries(["Gangnam Style", "2012", "PSY", "PSY","K-POP", None, None, None])
    db.change_value("tracks", "interpreter_id", "PSY", "interpreters", [("track_id =",1),])
    #db.remove_duplicates()
    db.output_table("tracks")
    #db.output_table("composers")
    #db.output_table("genres")
    #db.output_table("interpreters")
    #db.output_table("collections")
    #db.output_table("collections_tracks")
    for entry in db.get_entries():
        print(entry)