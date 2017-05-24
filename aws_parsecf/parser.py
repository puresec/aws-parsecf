from aws_parsecf.common import DELETE
from aws_parsecf.conditions import Conditions
from aws_parsecf.functions import Functions

class Parser:
    def __init__(self, root, default_region):
        self.functions = Functions(self, root, default_region)
        self.conditions = Conditions(self, root, default_region)

    def explode(self, current):
        # object
        if isinstance(current, dict):
            if '_exploded' in current:
                return
            current['_exploded'] = True

            # explode children first
            for key, value in current.items():
                self.exploded(current, key)

            condition_name = current.get('Condition')
            if condition_name and isinstance(condition_name, str):
                # condition
                if not self.conditions.evaluate(condition_name):
                    return DELETE
            elif len(current) == 2: # including '_exploded'
                # possibly a condition
                key, value = next((key, value) for key, value in current.items() if key != '_exploded')
                try:
                    return self.functions.evaluate(key, value)
                except KeyError as e:
                    if e.args != (key,):
                        raise
                    # not an intrinsic function
                if key != 'Condition': # 'Condition' means a name of a condtion, would make a mess
                    try:
                        return self.conditions.evaluate({key: value})
                    except KeyError as e:
                        if e.args != (key,):
                            raise
                        # not a condition
        # array
        elif isinstance(current, list):
            for index, value in enumerate(current):
                self.exploded(current, index)

    def cleanup(self, current):
        if isinstance(current, dict):
            if '_exploded' in current:
                del current['_exploded']
            for key, value in list(current.items()):
                if value is DELETE:
                    del current[key]
                else:
                    self.cleanup(value)
        elif isinstance(current, list):
            deleted = 0
            for index, value in enumerate(list(current)):
                if value is DELETE:
                    del current[index - deleted]
                    deleted += 1
                else:
                    self.cleanup(value)

    def exploded(self, collection, key):
        if collection[key] is None:
            return None
        exploded = self.explode(collection[key])
        if exploded is not None:
            collection[key] = exploded
        return collection[key]

