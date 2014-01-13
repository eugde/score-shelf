import os

class MyExeceptionBase(Exception):
    def __init__(self):
        self.message = ""

    def __str__(self):
        return self.message

class DuplicateError(MyExeceptionBase):
    def __init__(self, key):
        self.message = "Key '{}' already exists.".format(key)


class TypeAssessmentError(TypeError):
    def __init__(self, name, target_type):
        self.message = "Variable '{}' is '{}'. '{}' was expected.".format(name, type(name), target_type)

    def __str__(self):
        return self.message

class MissingTableError(MyExeceptionBase):
    def __init__(self, table_name, db_name):
        self.message = "The table {} doesn't exist in {}".format(table_name,db_name)

class InvalidColumnError(MyExeceptionBase):
    def __init__(self, table_names, invalid_columns, existing_columns):
        self.message = "The table(s) {} do(es) not contain all of these columns: {}".format(table_names, invalid_columns)
        self.detail_info = "The following columns exist: "
        for columns in existing_columns:
            self.detail_info += ", ".join(columns) + "\n"
