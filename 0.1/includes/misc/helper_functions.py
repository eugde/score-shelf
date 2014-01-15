__author__ = 'eugde'


def contains(source_list,search_list):
    """
    Checks if search_list contains all the elements from source_list.
    """

    for x in source_list:
        if x not in search_list:
            return False
    return True


def dict_factory(cursor, row):
    """
    An alternative for the default row_factory of sqlite which returns the data in a dictionairy.
    """

    data = {}
    for id_row, col in enumerate(cursor.description):
        data[col[0]] = row[id_row]
    return data

def nonesort(entry):
    if entry:
        return entry
    else:
        return ""

def create_placeholders(len):
    result = "( " + "?,"*(len-1) + "?)"
    return result