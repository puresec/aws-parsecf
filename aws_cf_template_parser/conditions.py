from common import DELETE

def evaluate(root, condition, default_region):
    if isinstance(condition, str):
        # condition name
        condition = _exploded(root, root['Conditions'], condition, default_region)
    if isinstance(condition, bool):
        # already evaluated
        return condition
    elif condition is DELETE:
        # type 'Condition' that was already evaluated
        return False

    # single-value dict with key as the type (see MAP)
    condition_type, value = next(iter(condition.items()))
    return MAP[condition_type](root, value, default_region)

def fn_and(root, value, default_region):
    """
    >>> fn_and(
    ...     {'Conditions':
    ...         {'AndCondition': {'Fn::And': [{'Fn::Equals': [1, 1]}, {'Fn::Equals': [2, 2]}]}}},
    ...     [{'Fn::Equals': [1, 1]}, {'Fn::Equals': [2, 2]}], 'us-east-1'
    ...     )
    True
    >>> fn_and(
    ...     {'Conditions':
    ...         {'AndCondition': {'Fn::And': [{'Fn::Equals': [1, 2]}, {'Fn::Equals': [2, 2]}]}}},
    ...     [{'Fn::Equals': [1, 2]}, {'Fn::Equals': [2, 2]}], 'us-east-1'
    ...     )
    False
    >>> fn_and(
    ...     {'Conditions':
    ...         {'AndCondition': {'Fn::And': [{'Fn::Equals': [1, 1]}, {'Fn::Equals': [1, 2]}]}}},
    ...     [{'Fn::Equals': [1, 1]}, {'Fn::Equals': [1, 2]}], 'us-east-1'
    ...     )
    False
    >>> fn_and(
    ...     {'Conditions':
    ...         {'AndCondition': {'Fn::And': [{'Fn::Equals': [1, 2]}, {'Fn::Equals': [1, 2]}]}}},
    ...     [{'Fn::Equals': [1, 2]}, {'Fn::Equals': [1, 2]}], 'us-east-1'
    ...     )
    False
    """

    return all(evaluate(root, condition, default_region) for condition in value)

def fn_equals(root, value, default_region):
    """
    >>> fn_equals(
    ...     {'Conditions':
    ...         {'EqualsCondition': {'Fn::Equals': [1, 1]}}},
    ...     [1, 1], 'us-east-1'
    ...     )
    True
    >>> fn_equals({'Conditions': {'EqualsCondition':
    ...     {'Fn::Equals': [1, 2]}}},
    ...     [1, 2], 'us-east-1'
    ...     )
    False
    """

    return all(part is not DELETE and part == value[0] for part in value)

def fn_not(root, value, default_region):
    """
    >>> fn_not(
    ...     {'Conditions':
    ...         {'NotCondition': {'Fn::Not': [{'Fn::Equals': [1, 1]}]}}},
    ...     [{'Fn::Equals': [1, 1]}], 'us-east-1'
    ...     )
    False
    >>> fn_not(
    ...     {'Conditions':
    ...         {'NotCondition': {'Fn::Not': [{'Fn::Equals': [1, 2]}]}}},
    ...     [{'Fn::Equals': [1, 2]}], 'us-east-1'
    ...     )
    True
    """

    condition, = value
    return not evaluate(root, condition, default_region)

def fn_or(root, value, default_region):
    """
    >>> fn_or(
    ...     {'Conditions':
    ...         {'OrCondition': {'Fn::Or': [{'Fn::Equals': [1, 1]}, {'Fn::Equals': [2, 2]}]}}},
    ...     [{'Fn::Equals': [1, 1]}, {'Fn::Equals': [2, 2]}], 'us-east-1'
    ...     )
    True
    >>> fn_or(
    ...     {'Conditions':
    ...         {'OrCondition': {'Fn::Or': [{'Fn::Equals': [1, 2]}, {'Fn::Equals': [2, 2]}]}}},
    ...     [{'Fn::Equals': [1, 2]}, {'Fn::Equals': [2, 2]}], 'us-east-1'
    ...     )
    True
    >>> fn_or(
    ...     {'Conditions':
    ...         {'OrCondition': {'Fn::Or': [{'Fn::Equals': [1, 1]}, {'Fn::Equals': [1, 2]}]}}},
    ...     [{'Fn::Equals': [1, 1]}, {'Fn::Equals': [1, 2]}], 'us-east-1'
    ...     )
    True
    >>> fn_or(
    ...     {'Conditions':
    ...         {'OrCondition': {'Fn::Or': [{'Fn::Equals': [1, 2]}, {'Fn::Equals': [1, 2]}]}}},
    ...     [{'Fn::Equals': [1, 2]}, {'Fn::Equals': [1, 2]}], 'us-east-1'
    ...     )
    False
    """

    return any(evaluate(root, condition, default_region) for condition in value)

MAP = {
        'Condition': evaluate,
        'Fn::And': fn_and,
        'Fn::Equals': fn_equals,
        'Fn::Not': fn_not,
        'Fn::Or': fn_or,
        }

from parser import _exploded
