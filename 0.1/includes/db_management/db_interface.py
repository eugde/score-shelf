import sys
import random
import sqlite3

from misc.myExceptions import MissingTableError, InvalidColumnError
from misc.helper_functions import contains, dict_factory


class DbHandler:
    """
    This class handles all database-related operations in the program.
    """

    def __init__(self, db_name):
        """
        Creates a new DbHandler-Object to a new or existing database. A cursor-object is also initiated.

        @param db_name: The name of the database, if an invaid name is given a random number will be generated as name.
        """

        self.db_name = db_name
        self.conversion_list = {"int": "INTEGER", "None": "NULL", "float":"REAL", "bytes": "TEXT", "str": "TEXT"}

        try:
            self.db_connection = sqlite3.connect(self.db_name)
        except TypeError:
            self.db_name = str(random.randint(99999, 999999)) + ".db"
            self.db_connection = sqlite3.connect(self.db_name)
        except sqlite3.Error as e:
            print("Error: "+e.args[0])

        self.cursor = self.db_connection.cursor()
        self.tables = []
        self.fetch_table_list()
        self.db_information = {}
        self.update_db_description()

    #Table-Management

    def create_table(self, table_name, cols):
        """
        Creates a new table with the given columns.

        @param table_name: Name of the new table.
        Note: If this is the name of an existing table, it will not override the old table.

        @param cols: The columns of the new table.
        Must be a dictionary containing pairs of names and corresponding SQL-types such as {'id': 'INTEGER'}
        """

        sql = "CREATE TABLE IF NOT EXISTS {} (".format(table_name)

        for entry in cols:
            sql += "{} {},".format(entry[0],entry[1])

        sql = str(sql.rsplit(",", 1)[0])
        sql += " )"

        #print(sql)

        with self.db_connection:
            self.cursor.execute(sql)
        self.fetch_table_list()

    def alter_table(self, table_name, cols):
        """
        Takes an existing table and alters its columns.
        NOTE: If the new table doesn't contain all the columns of the old table data can get lost!

        @param table_name: A string containing the name of the table to be altered.
        @param cols: A list of tuples containing the columns for the new table.
        """

        self.fetch_table_list()
        temp_table_name = table_name+"_temp"
        try:
            if table_name in self.tables:
                sql_alter_temp_statement = "ALTER TABLE {} RENAME TO {}".format(table_name,temp_table_name)
                with self.db_connection:
                    self.cursor.execute(sql_alter_temp_statement)
                self.fetch_table_list()
            else:
                raise MissingTableError(table_name, self.db_name)
        except MissingTableError as e:
            print(e.message)
            sys.exit(0)

        self.create_table(table_name, cols)
        print(self.tables)

        old_columns = self.fetch_table_description(temp_table_name)
        new_columns = [x[0] for x in cols]
        columns_to_copy = [x for x in new_columns if x in old_columns]
        print("COPY COLUMNS ",columns_to_copy)

        self.copy_data_into_table(temp_table_name, table_name, columns_to_copy)
        self.drop_table(temp_table_name)

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

        try:
            # The if-statement is used as alternative protection against sql-injection because of the string-formatting
            # in the sql statement.
            if table_name in self.tables:
                sql = "DROP TABLE IF EXISTS {}".format(table_name)
                with self.db_connection:
                    self.cursor.execute(sql)
                    self.fetch_table_list()
                    print("Table {} dropped!".format(table_name))
            else:
                raise MissingTableError(table_name, self.db_name)
        except MissingTableError as e:
            print(e.message)

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

            if ordered_keys:
                with self.db_connection:
                    #print(sql)
                    self.cursor.execute(sql)

    def delete_from_table(self, table_name, col, value):
        """
        Deletes rows from the table 'table_name' where 'col' = 'value'

        @table_name: A string containing the name of the target table.
        @col: The column in the table containing the value for the WHERE-clause
        @value: The value the WHERE-clause checks against.
        """

        try:
            if table_name in self.tables:
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

        with self.db_connection:
            #print(sql, sql_parameters)
            #print(tuple(sql_parameters))
            self.cursor.execute(sql,tuple(sql_parameters))

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

        self.fetch_table_list()
        try:
            if table_name in self.tables:
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
        @return:
        """

        try:
            if table_name in self.tables:
                print(table_name.upper())
                for col in self.fetch_table_description("test"):
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


if __name__ == "__main__":
    db = DbHandler("data/test.db")
    #db.drop_table("test")
    db.create_table("test", [("id","INTEGER PRIMARY KEY"),("name","TEXT"), ("link_guitar","TEXT")])
    #db.insert_into_table("test", {"name": "Hallo Welt"},{"name":"Tschüss Welt", "link_guitar": "asdf"},{"denkeygibtsned":"asdf"})

    db.output_table("test")
    db.update_table("test", [("name", "H4ll0 W3lt"), [("id =", 1)], ("link_guitar", "Bass")] )
    #db.output_table("test")
    #db.alter_table("test", [("id","INTEGER PRIMARY KEY"),("name","TEXT"), ("link_guitar","TEXT"), ("link_bass", "TEXT")])
    #db.output_table("test")

    print(db.tables)
    table_data = db.fetch_table("test", ["id","name"], condition=[("id >", 2), ("id<",5)], dict_output=False)
    print (table_data)

    print(db.fetch_table("test"))