from aws_parsecf.common import DELETE
import base64
import boto3
import re

class Functions:
    def __init__(self, parser, root, default_region):
        self.parser = parser
        self.root = root
        self.default_region = default_region

    MAP = {
            'Fn::Base64': 'fn_base64',
            'Fn::If': 'fn_if',
            'Fn::FindInMap': 'fn_find_in_map',
            'Fn::GetAtt': 'fn_get_att',
            'Fn::GetAZs': 'fn_get_azs',
            'Fn::ImportValue': 'fn_import_value',
            'Fn::Join': 'fn_join',
            'Fn::Select': 'fn_select',
            'Fn::Split': 'fn_split',
            'Fn::Sub': 'fn_sub',
            'Ref': 'ref',
            }

    def evaluate(self, function_type, value):
        return getattr(self, Functions.MAP[function_type])(value)

    def fn_base64(self, value):
        """
        >>> str(Functions(None, # 2.7 represents this as u'...'
        ...     {'Fn::Base64': 'hello'},
        ...     'us-east-1'
        ...     ).fn_base64('hello'))
        'aGVsbG8='
        """
        if isinstance(value, str):
            value = value.encode()
        return base64.b64encode(value).decode()

    def fn_if(self, value):
        """
        >>> from aws_parsecf.parser import Parser

        >>> root = {'Conditions': {'EqualsCondition': {'Fn::Equals': [1, 1]}},
        ...         'Fn::If': ['EqualsCondition', 10, 20]}
        >>> Functions(Parser(root, 'us-east-1'),
        ...     root,
        ...     'us-east-1'
        ...     ).fn_if(['EqualsCondition', 10, 20])
        10

        >>> root = {'Conditions': {'EqualsCondition': {'Fn::Equals': [1, 2]}},
        ...         'Fn::If': ['EqualsCondition', 10, 20]}
        >>> Functions(Parser(root, 'us-east-1'),
        ...     root,
        ...     'us-east-1'
        ...     ).fn_if(['EqualsCondition', 10, 20])
        20
        """

        condition_name, true_value, false_value = value
        if self.parser.conditions.evaluate(condition_name):
            return true_value
        else:
            return false_value

    def fn_find_in_map(self, value):
        """
        >>> from aws_parsecf.parser import Parser

        >>> root = {'Mappings': {'RegionMap':
        ...             {'us-east-1': {'32': 'ami-6411e20d', '64': 'ami-7a11e213'},
        ...             'us-west-1': { '32' : 'ami-c9c7978c', '64' : 'ami-cfc7978a'}}},
        ...         'Fn::FindInMap': ['RegionMap', 'us-west-1', '32']}
        >>> Functions(Parser(root, 'us-east-1'),
        ...     root,
        ...     'us-east-1'
        ...     ).fn_find_in_map(['RegionMap', 'us-west-1', '32'])
        'ami-c9c7978c'

        >>> root = {'Conditions': {'EqualsCondition': {'Fn::Equals': [1, 1]}},
        ...         'Mappings': {'RegionMap':
        ...             {'us-east-1': {'Fn::If': ['EqualsCondition', 'ami-c9c7978c', 'ami-cfc7978a']}}},
        ...         'Fn::FindInMap': ['RegionMap', 'us-east-1']}
        >>> Functions(Parser(root, 'us-east-1'),
        ...     root,
        ...     'us-east-1'
        ...     ).fn_find_in_map(['RegionMap', 'us-east-1'])
        'ami-c9c7978c'
        """

        current = self.root['Mappings']
        for index, key in enumerate(value):
            current = self.parser.exploded(current, key)
        return current

    def fn_get_att(self, value):
        """
        >>> from aws_parsecf.parser import Parser

        >>> root = {'Resources':
        ...             {'SomeResource': {'Properties': {'SomeKey': 'SomeValue'}}},
        ...         'Fn::GetAtt': ['SomeResource', 'SomeKey']}
        >>> Functions(Parser(root, 'us-east-1'),
        ...     root,
        ...     'us-east-1'
        ...     ).fn_get_att(['SomeResource', 'SomeKey'])
        'SomeValue'

        >>> root = {'Resources':
        ...             {'SomeResource': {'Properties': {'List': [{'SomeKey': 'SomeValue'}]}}},
        ...         'Fn::GetAtt': ['SomeResource', 'SomeKey']}
        >>> Functions(Parser(root, 'us-east-1'),
        ...     root,
        ...     'us-east-1'
        ...     ).fn_get_att(['SomeResource', 'SomeKey'])
        'SomeValue'

        >>> root = {'Fn::GetAtt': ['SomeResource', 'SomeKey']}
        >>> Functions(Parser(root, 'us-east-1'),
        ...     root,
        ...     'us-east-1'
        ...     ).fn_get_att(['SomeResource', 'SomeKey'])
        'UNKNOWN ATT: SomeResource.SomeKey'

        >>> root = {'Resources': {},
        ...         'Fn::GetAtt': ['SomeResource', 'SomeKey']}
        >>> Functions(Parser(root, 'us-east-1'),
        ...     root,
        ...     'us-east-1'
        ...     ).fn_get_att(['SomeResource', 'SomeKey'])
        'UNKNOWN ATT: SomeResource.SomeKey'
        """

        resource_name, key = value
        if resource_name in self.root.get('Resources', ()):
            resource = self.parser.exploded(self.root['Resources'], resource_name)
            try:
                return self._find_att(resource, key)
            except KeyError as e:
                if e.args != (key,):
                    raise

        return "UNKNOWN ATT: {}.{}".format(resource_name, key)

    def fn_get_azs(self, value):
        """
        >>> import os
        >>> if os.environ.get('FULL'):
        ...     Functions(None,
        ...         {'Fn::GetAZs': ''},
        ...         'us-east-1'
        ...         ).fn_get_azs('')
        ...     Functions(None,
        ...         {'Fn::GetAZs': 'us-west-1'},
        ...         'us-east-1'
        ...         ).fn_get_azs('us-west-1')
        ... else:
        ...     print(['us-east-1a', 'us-east-1b', 'us-east-1c', 'us-east-1d', 'us-east-1e'])
        ...     print(['us-west-1a', 'us-west-1c'])
        ['us-east-1a', 'us-east-1b', 'us-east-1c', 'us-east-1d', 'us-east-1e']
        ['us-west-1a', 'us-west-1c']
        """

        # NOTE: If you change this function, please run the tests with FULL=true environment variable!
        return [
                zone['ZoneName'] for zone in
                boto3.client('ec2', region_name=value or self.default_region).describe_availability_zones()['AvailabilityZones']
                ]

    def fn_import_value(self, value):
        if not hasattr(self, '_import_value_cache'):
            self._import_value_cache = dict(
                    (export['Name'], export['Value']) for export in
                    boto3.client('cloudformation', region_name=self.default_region).list_exports()['Exports']
                    )
        return self._import_value_cache.get(value, "UNKNOWN IMPORT VALUE: {}".format(value))

    def fn_join(self, value):
        """
        >>> Functions(None,
        ...     {'Fn::Join': [':', ['a', 'b', 'c']]},
        ...     'us-east-1'
        ...     ).fn_join([':', ['a', 'b', 'c']])
        'a:b:c'
        """

        delimeter, values = value
        return delimeter.join(values)

    def fn_select(self, value):
        """
        >>> Functions(None,
        ...     {'Fn::Select': ['1', ['a', 'b', 'c', 'd', 'e']]},
        ...     'us-east-1'
        ...     ).fn_select(['1', ['a', 'b', 'c', 'd', 'e']])
        'b'
        """

        index, values = value
        return values[int(index)]

    def fn_split(self, value):
        """
        >>> Functions(None,
        ...     {'Fn::Split': ['|', 'a|b|c']},
        ...     'us-east-1'
        ...     ).fn_split(['|', 'a|b|c'])
        ['a', 'b', 'c']
        """

        delimeter, value = value
        return value.split(delimeter)

    def fn_sub(self, value):
        """
        >>> from aws_parsecf.parser import Parser

        >>> root = {'Fn::Sub': ['hello-${Who} ${When}', {'Who': 'world', 'When': 'NOW'}]}
        >>> Functions(Parser(root, 'us-east-1'),
        ...     root,
        ...     'us-east-1'
        ...     ).fn_sub(['hello-${Who} ${When}', {'Who': 'world', 'When': 'NOW'}])
        'hello-world NOW'

        >>> root = {'Fn::Sub': 'hello world'}
        >>> Functions(Parser(root, 'us-east-1'),
        ...     root,
        ...     'us-east-1'
        ...     ).fn_sub('hello world')
        'hello world'

        >>> root = {'Resources':
        ...             {'SomeResource': {'Properties': {'SomeKey': 'SomeValue'}}},
        ...         'Fn::Sub': 'hello ${SomeResource.SomeKey}'}
        >>> Functions(Parser(root, 'us-east-1'),
        ...     root,
        ...     'us-east-1'
        ...     ).fn_sub('hello ${SomeResource.SomeKey}')
        'hello SomeValue'

        >>> root = {'Resources':
        ...             {'SomeResource': {'Properties': {'SomeKey': 'SomeValue'}}},
        ...         'Fn::Sub': 'hello ${!SomeResource.SomeKey}'}
        >>> Functions(Parser(root, 'us-east-1'),
        ...     root,
        ...     'us-east-1'
        ...     ).fn_sub('hello ${!SomeResource.SomeKey}')
        'hello ${SomeResource.SomeKey}'
        """

        if isinstance(value, list):
            value, variables = value
        else:
            # only template parameter names, resource logical IDs, and resource attributes, will be parsed
            value, variables = value, {}

        for name, target in variables.items():
            value = value.replace('${{{}}}'.format(name), target)

        return Functions.SUB_VARIABLE_PATTERN.sub(self._sub_variable, value)

    def ref(self, value):
        """
        >>> from aws_parsecf.parser import Parser

        >>> root = {'Ref': 'AWS::Region'}
        >>> Functions(Parser(root, 'us-east-1'),
        ...     root,
        ...     'us-east-1'
        ...     ).ref('AWS::Region')
        'us-east-1'

        >>> root = {'Ref': 'AWS::NoValue'}
        >>> Functions(Parser(root, 'us-east-1'),
        ...     root,
        ...     'us-east-1'
        ...     ).ref('AWS::NoValue')
        DELETE

        >>> root = {'Resources':
        ...             {'SomeFunction': {'Type': 'AWS::Lambda::Function', 'Properties': {'FunctionName': 'SomeFunctionName'}}},
        ...         'Ref': 'SomeFunction'}
        >>> Functions(Parser(root, 'us-east-1'),
        ...     root,
        ...     'us-east-1'
        ...     ).ref('SomeFunction')
        'SomeFunctionName'

        >>> root = {'Resources':
        ...             {'SomeFunction': {'Type': 'AWS::Lambda::Function', 'Properties': {}}},
        ...         'Ref': 'SomeFunction'}
        >>> Functions(Parser(root, 'us-east-1'),
        ...     root,
        ...     'us-east-1'
        ...     ).ref('SomeFunction')
        'UNKNOWN REF: SomeFunction'

        >>> root = {'Ref': 'SomeValue'}
        >>> Functions(Parser(root, 'us-east-1'),
        ...     root,
        ...     'us-east-1'
        ...     ).ref('SomeValue')
        'UNKNOWN REF: SomeValue'
        """

        # pseudo function?
        function = Functions.REF_PSEUDO_FUNCTIONS.get(value)
        if function:
            return function(self)
        # resource logical id?
        if value in self.root.get('Resources', ()):
            resource = self.parser.exploded(self.root['Resources'], value)
            name_type = Functions.REF_RESOURCE_TYPE_PATTERN.match(resource['Type'])
            if name_type:
                name = resource.get('Properties', {}).get("{}Name".format(name_type.group(1)))
                if name:
                    return name

        return "UNKNOWN REF: {}".format(value)

    def _find_att(self, current, key):
        if isinstance(current, dict):
            if key in current:
                return current[key]
            for value in current.values():
                try:
                    result = self._find_att(value, key)
                except KeyError as e:
                    if e.args != (key,):
                        raise
                    continue
                return result
        elif isinstance(current, list):
            for value in current:
                try:
                    result = self._find_att(value, key)
                except KeyError as e:
                    if e.args != (key,):
                        raise
                    continue
                return result
        raise KeyError(key)

    SUB_VARIABLE_PATTERN = re.compile(r"\${(.+)}")
    def _sub_variable(self, match):
        variable = match.group(1)
        if variable.startswith('!'):
            return "${{{}}}".format(variable[1:])
        elif '.' in variable:
            return self.fn_get_att(variable.split('.'))
        else:
            return self.ref(variable)

    REF_PSEUDO_FUNCTIONS = {
            'AWS::NoValue': lambda self: DELETE,
            'AWS::Region': lambda self: self.default_region,
            }

    REF_RESOURCE_TYPE_PATTERN = re.compile(r"^.+::(.+?)$")

