from aws_parsecf.common import DELETE
from functools import partial
import base64
import boto3
import re

def evaluate(root, function_type, value, default_region):
    return MAP[function_type](root, value, default_region)

def fn_base64(root, value, default_region):
    """
    >>> fn_base64({'Fn::Base64': 'hello'}, 'hello', 'us-east-1')
    'aGVsbG8='
    """
    if isinstance(value, str):
        value = value.encode()
    return base64.b64encode(value).decode()

def fn_if(root, value, default_region):
    """
    >>> fn_if(
    ...     {'Conditions': {'EqualsCondition': {'Fn::Equals': [1, 1]}},
    ...      'Fn::If': ['EqualsCondition', 10, 20]},
    ...     ['EqualsCondition', 10, 20], 'us-east-1'
    ...     )
    10
    >>> fn_if(
    ...     {'Conditions': {'EqualsCondition': {'Fn::Equals': [1, 2]}},
    ...      'Fn::If': ['EqualsCondition', 10, 20]},
    ...     ['EqualsCondition', 10, 20], 'us-east-1'
    ...     )
    20
    """

    condition_name, true_value, false_value = value
    if conditions.evaluate(root, condition_name, default_region):
        return true_value
    else:
        return false_value

def fn_find_in_map(root, value, default_region):
    """
    >>> fn_find_in_map(
    ...     {'Mappings': {'RegionMap':
    ...         {'us-east-1': {'32': 'ami-6411e20d', '64': 'ami-7a11e213'},
    ...          'us-west-1': { '32' : 'ami-c9c7978c', '64' : 'ami-cfc7978a'}}},
    ...      'Fn::FindInMap': ['RegionMap', 'us-west-1', '32']},
    ...     ['RegionMap', 'us-west-1', '32'], 'us-east-1'
    ...     )
    'ami-c9c7978c'
    >>> fn_find_in_map(
    ...     {'Conditions': {'EqualsCondition': {'Fn::Equals': [1, 1]}},
    ...      'Mappings': {'RegionMap':
    ...         {'us-east-1': {'Fn::If': ['EqualsCondition', 'ami-c9c7978c', 'ami-cfc7978a']}}},
    ...      'Fn::FindInMap': ['RegionMap', 'us-east-1']},
    ...     ['RegionMap', 'us-east-1'], 'us-east-1'
    ...     )
    'ami-c9c7978c'
    """

    current = root['Mappings']
    for index, key in enumerate(value):
        current = _exploded(root, current, key, default_region)
    return current

def fn_get_att(root, value, default_region):
    """
    >>> fn_get_att(
    ...     {'Resources':
    ...         {'SomeResource': {'Properties': {'SomeKey': 'SomeValue'}}},
    ...      'Fn::GetAtt': ['SomeResource', 'SomeKey']},
    ...     ['SomeResource', 'SomeKey'], 'us-east-1'
    ...     )
    'SomeValue'
    >>> fn_get_att(
    ...     {'Resources':
    ...         {'SomeResource': {'Properties': {'List': [{'SomeKey': 'SomeValue'}]}}},
    ...      'Fn::GetAtt': ['SomeResource', 'SomeKey']},
    ...     ['SomeResource', 'SomeKey'], 'us-east-1'
    ...     )
    'SomeValue'
    >>> fn_get_att(
    ...     {'Resources': {'SomeResource': {}},
    ...      'Fn::GetAtt': ['SomeResource', 'SomeKey']},
    ...     ['SomeResource', 'SomeKey'], 'us-east-1'
    ...     )
    'UNKNOWN ATT: SomeResource.SomeKey'
    """

    resource_name, key = value
    resource = _exploded(root, root['Resources'], resource_name, default_region)
    try:
        return _find_att(root, resource, key, default_region)
    except KeyError as e:
        if e.args != (key,):
            raise
        return "UNKNOWN ATT: {}.{}".format(resource_name, key)

def fn_get_azs(root, value, default_region):
    """
    >>> import os
    >>> if os.environ.get('FULL'):
    ...     fn_get_azs(
    ...         {'Fn::GetAZs': ''},
    ...         '', 'us-east-1'
    ...         )
    ...     fn_get_azs(
    ...         {'Fn::GetAZs': 'us-west-1'},
    ...         'us-west-1', 'us-east-1'
    ...         )
    ... else:
    ...     print('To run this test use FULL=true')
    ['us-east-1a', 'us-east-1b', 'us-east-1c', 'us-east-1d', 'us-east-1e']
    ['us-west-1a', 'us-west-1c']
    """

    return [
            zone['ZoneName'] for zone in
            boto3.client('ec2', region_name=value or default_region).describe_availability_zones()['AvailabilityZones']
            ]

def fn_import_value(root, value, default_region):
    pass

def fn_join(root, value, default_region):
    """
    >>> fn_join(
    ...     {'Fn::Join': [':', ['a', 'b', 'c']]},
    ...     [':', ['a', 'b', 'c']], 'us-east-1'
    ...     )
    'a:b:c'
    """

    delimeter, values = value
    return delimeter.join(values)

def fn_select(root, value, default_region):
    """
    >>> fn_select(
    ...     {'Fn::Select': ['1', ['a', 'b', 'c', 'd', 'e']]},
    ...     ['1', ['a', 'b', 'c', 'd', 'e']], 'us-east-1'
    ...     )
    'b'
    """

    index, values = value
    return values[int(index)]

def fn_split(root, value, default_region):
    """
    >>> fn_split(
    ...     {'Fn::Split': ['|', 'a|b|c']},
    ...     ['|', 'a|b|c'], 'us-east-1'
    ...     )
    ['a', 'b', 'c']
    """

    delimeter, value = value
    return value.split(delimeter)

def fn_sub(root, value, default_region):
    """
    >>> fn_sub(
    ...     {'Fn::Sub': ['hello-${Who} ${When}', {'Who': 'world', 'When': 'NOW'}]},
    ...     ['hello-${Who} ${When}', {'Who': 'world', 'When': 'NOW'}], 'us-east-1'
    ...     )
    'hello-world NOW'
    >>> fn_sub(
    ...     {'Fn::Sub': 'hello world'},
    ...     'hello world', 'us-east-1'
    ...     )
    'hello world'
    >>> fn_sub(
    ...     {'Resources':
    ...         {'SomeResource': {'Properties': {'SomeKey': 'SomeValue'}}},
    ...      'Fn::Sub': 'hello ${SomeResource.SomeKey}'},
    ...      'hello ${SomeResource.SomeKey}', 'us-east-1'
    ...     )
    'hello SomeValue'
    >>> fn_sub(
    ...     {'Resources':
    ...         {'SomeResource': {'Properties': {'SomeKey': 'SomeValue'}}},
    ...      'Fn::Sub': 'hello ${!SomeResource.SomeKey}'},
    ...      'hello ${!SomeResource.SomeKey}', 'us-east-1'
    ...     )
    'hello ${SomeResource.SomeKey}'
    """

    if isinstance(value, list):
        value, variables = value
    else:
        # only template parameter names, resource logical IDs, and resource attributes, will be parsed
        value, variables = value, {}

    for name, target in variables.items():
        value = value.replace('${{{}}}'.format(name), target)

    return SUB_VARIABLE_PATTERN.sub(partial(_sub_variable, root, default_region), value)

def ref(root, value, default_region):
    """
    >>> ref(
    ...     {'Ref': 'AWS::Region'},
    ...     'AWS::Region', 'us-east-1'
    ...     )
    'us-east-1'
    >>> ref(
    ...     {'Ref': 'AWS::NoValue'},
    ...     'AWS::NoValue', 'us-east-1'
    ...     )
    DELETE
    >>> ref(
    ...     {'Resources':
    ...         {'SomeFunction': {'Type': 'AWS::Lambda::Function', 'Properties': {'FunctionName': 'SomeFunctionName'}}},
    ...      'Ref': 'SomeFunction'},
    ...     'SomeFunction', 'us-east-1'
    ...     )
    'SomeFunctionName'
    >>> ref(
    ...     {'Resources':
    ...         {'SomeFunction': {'Type': 'AWS::Lambda::Function', 'Properties': {}}},
    ...      'Ref': 'SomeFunction'},
    ...     'SomeFunction', 'us-east-1'
    ...     )
    'UNKNOWN REF: SomeFunction'
    >>> ref(
    ...     {'Ref': 'SomeValue'},
    ...     'SomeValue', 'us-east-1'
    ...     )
    'UNKNOWN REF: SomeValue'
    """

    # pseudo function?
    function = REF_PSEUDO_FUNCTIONS.get(value)
    if function:
        return function(root, default_region)
    # resource logical id?
    if value in root.get('Resources', ()):
        resource = _exploded(root, root['Resources'], value, default_region)
        name_type = REF_RESOURCE_TYPE_PATTERN.match(resource['Type'])
        if name_type:
            name = resource['Properties'].get("{}Name".format(name_type.group(1)))
            if name:
                return name

    return "UNKNOWN REF: {}".format(value)

MAP = {
        'Fn::Base64': fn_base64,
        'Fn::If': fn_if,
        'Fn::FindInMap': fn_find_in_map,
        'Fn::GetAtt': fn_get_att,
        'Fn::GetAZs': fn_get_azs,
        'Fn::ImportValue': fn_import_value,
        'Fn::Join': fn_join,
        'Fn::Select': fn_select,
        'Fn::Split': fn_split,
        'Fn::Sub': fn_sub,
        'Ref': ref,
        }

from aws_parsecf.parser import _exploded
from aws_parsecf import conditions

def _find_att(root, current, key, default_region):
    if isinstance(current, dict):
        if key in current:
            return current[key]
        for value in current.values():
            try:
                result = _find_att(root, value, key, default_region)
            except KeyError as e:
                if e.args != (key,):
                    raise
                continue
            return result
    elif isinstance(current, list):
        for value in current:
            try:
                result = _find_att(root, value, key, default_region)
            except KeyError as e:
                if e.args != (key,):
                    raise
                continue
            return result
    raise KeyError(key)

SUB_VARIABLE_PATTERN = re.compile(r"\${(.+)}")
def _sub_variable(root, default_region, match):
    variable = match.group(1)
    if variable.startswith('!'):
        return "${{{}}}".format(variable[1:])
    elif '.' in variable:
        return fn_get_att(root, variable.split('.'), default_region)
    else:
        return fn_get_ref(root, variable, default_region)

REF_PSEUDO_FUNCTIONS = {
        'AWS::NoValue': lambda root, default_region: DELETE,
        'AWS::Region': lambda root, default_region: default_region,
        }

REF_RESOURCE_TYPE_PATTERN = re.compile(r"^.+::(.+?)$")

