# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #
#   AUTHORS :           Nicolas Dorey
#                       Sophie Chauvet
#                       Romain Leclerc
#                       Maximillien Rolland
#
#   DESCRIPTION :       Reads dicts libs
#
#   Update  1.0.0 :     We start here.
#
#   KnownBugs :         None atm.
# ------------------------------------------------------------------------------------------------------------------------------------- #
# ------------------------------------------------------------------------------------------------------------------------------------- #


# TODO: snakecase
def get_key_by_value(dictOfElements, valueToFind):
    """
    Return the key of the value given for the dict.
    Exemple : dict = {1 : "Toto", 2 : "Tata"}
    valueToFind="Tata"  ===> fonction returns 1
    :param: valueToFind => value of dictionnary to find
    :type: dict item value
    :return: listOfKeys => the list of the keys that corresponds to the value.
    :rtype: list
    """
    listOfKeys = list()
    listOfItems = dictOfElements.items()
    for item in listOfItems:
        if item[1] == valueToFind:
            listOfKeys.append(item[0])
    return listOfKeys


def find_value_recursively(d, key):
    """
    :param: d, key
    """
    for k, v in d.iteritems():
        if isinstance(v, dict):
            find_value_recursively(v, key)
        else:
            if k is key:
                print("found value for {}: {}".format(key, v))


def get_dict_value_repeat(dict):
    """
    Creates a new dict with {value:nbOfRepeat} of dict given.
    :param: dict => dict with list {Value1 : [bidule, chouette], Value2, [bidule, truc]}
    :return: repeat => dict with nb of repeat. {bidule: 2}
    :rtype: dict
    """
    repeat = {}
    i = 0
    for key, values in dict.items():
        if key not in repeat:
            if type(values) == list:
                for value in values:
                    if value in repeat:
                        repeat[value] += 1
                    else:
                        repeat[value] = 1
        i += 1
    return repeat
