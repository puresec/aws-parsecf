from aws_parsecf.common import DELETE

class Conditions:
    def __init__(self, parser, root, default_region):
        self.parser = parser
        self.root = root
        self.default_region = default_region

    MAP = {
            'Condition': 'evaluate',
            'Fn::And': 'fn_and',
            'Fn::Equals': 'fn_equals',
            'Fn::Not': 'fn_not',
            'Fn::Or': 'fn_or',
            }

    def evaluate(self, condition):
        if isinstance(condition, str):
            # condition name
            condition = self.parser.exploded(self.root['Conditions'], condition)
        if isinstance(condition, bool):
            # already evaluated
            return condition
        elif condition is DELETE:
            # type 'Condition' that was already evaluated
            return False

        # single-value dict with key as the type (see Conditions.MAP)
        condition_type, value = next(iter(condition.items()))
        return getattr(self, Conditions.MAP[condition_type])(value)

    def fn_and(self, value):
        """
        >>> Conditions(None,
        ...     {'Conditions':
        ...         {'AndCondition': {'Fn::And': [{'Fn::Equals': [1, 1]}, {'Fn::Equals': [2, 2]}]}}},
        ...     'us-east-1'
        ...     ).fn_and([{'Fn::Equals': [1, 1]}, {'Fn::Equals': [2, 2]}])
        True
        >>> Conditions(None,
        ...     {'Conditions':
        ...         {'AndCondition': {'Fn::And': [{'Fn::Equals': [1, 2]}, {'Fn::Equals': [2, 2]}]}}},
        ...     'us-east-1'
        ...     ).fn_and([{'Fn::Equals': [1, 2]}, {'Fn::Equals': [2, 2]}])
        False
        >>> Conditions(None,
        ...     {'Conditions':
        ...         {'AndCondition': {'Fn::And': [{'Fn::Equals': [1, 1]}, {'Fn::Equals': [1, 2]}]}}},
        ...     'us-east-1'
        ...     ).fn_and([{'Fn::Equals': [1, 1]}, {'Fn::Equals': [1, 2]}])
        False
        >>> Conditions(None,
        ...     {'Conditions':
        ...         {'AndCondition': {'Fn::And': [{'Fn::Equals': [1, 2]}, {'Fn::Equals': [1, 2]}]}}},
        ...     'us-east-1'
        ...     ).fn_and([{'Fn::Equals': [1, 2]}, {'Fn::Equals': [1, 2]}])
        False
        """

        return all(self.evaluate(condition) for condition in value)

    def fn_equals(self, value):
        """
        >>> Conditions(None,
        ...     {'Conditions':
        ...         {'EqualsCondition': {'Fn::Equals': [1, 1]}}},
        ...     'us-east-1'
        ...     ).fn_equals([1, 1])
        True
        >>> Conditions(None,
        ...     {'Conditions': {'EqualsCondition':
        ...         {'Fn::Equals': [1, 2]}}},
        ...     'us-east-1'
        ...     ).fn_equals([1, 2])
        False
        """

        return all(part is not DELETE and part == value[0] for part in value)

    def fn_not(self, value):
        """
        >>> Conditions(None,
        ...     {'Conditions':
        ...         {'NotCondition': {'Fn::Not': [{'Fn::Equals': [1, 1]}]}}},
        ...     'us-east-1'
        ...     ).fn_not([{'Fn::Equals': [1, 1]}])
        False
        >>> Conditions(None,
        ...     {'Conditions':
        ...         {'NotCondition': {'Fn::Not': [{'Fn::Equals': [1, 2]}]}}},
        ...     'us-east-1'
        ...     ).fn_not([{'Fn::Equals': [1, 2]}])
        True
        """

        condition, = value
        return not self.evaluate(condition)

    def fn_or(self, value):
        """
        >>> Conditions(None,
        ...     {'Conditions':
        ...         {'OrCondition': {'Fn::Or': [{'Fn::Equals': [1, 1]}, {'Fn::Equals': [2, 2]}]}}},
        ...     'us-east-1'
        ...     ).fn_or([{'Fn::Equals': [1, 1]}, {'Fn::Equals': [2, 2]}])
        True
        >>> Conditions(None,
        ...     {'Conditions':
        ...         {'OrCondition': {'Fn::Or': [{'Fn::Equals': [1, 2]}, {'Fn::Equals': [2, 2]}]}}},
        ...     'us-east-1'
        ...     ).fn_or([{'Fn::Equals': [1, 2]}, {'Fn::Equals': [2, 2]}])
        True
        >>> Conditions(None,
        ...     {'Conditions':
        ...         {'OrCondition': {'Fn::Or': [{'Fn::Equals': [1, 1]}, {'Fn::Equals': [1, 2]}]}}},
        ...     'us-east-1'
        ...     ).fn_or([{'Fn::Equals': [1, 1]}, {'Fn::Equals': [1, 2]}])
        True
        >>> Conditions(None,
        ...     {'Conditions':
        ...         {'OrCondition': {'Fn::Or': [{'Fn::Equals': [1, 2]}, {'Fn::Equals': [1, 2]}]}}},
        ...     'us-east-1'
        ...     ).fn_or([{'Fn::Equals': [1, 2]}, {'Fn::Equals': [1, 2]}])
        False
        """

        return any(self.evaluate(condition) for condition in value)

