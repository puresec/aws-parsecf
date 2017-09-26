class Delete:
    def __repr__(self):
        return 'DELETE'

DELETE = Delete()

class UnknownValue(str):
    def __new__(cls, key):
        obj = str.__new__(cls, "UNKNOWN {}".format(key))
        obj.key = key
        return obj

