from aws_parsecf.common import DELETE
import boto3
import json
import yaml

def load_json(stream, default_region=boto3.Session().region_name):
    return _explode(json.load(stream), default_region)

def loads_json(string, default_region=boto3.Session().region_name):
    return _explode(string.loads(string), default_region)

def load_yaml(stream_or_string, default_region=boto3.Session().region_name):
    return _explode(yaml.load(stream_or_string), default_region)

def _explode(root, default_region, current=None):
    """
    >>> import json

    >>> print(json.dumps(_explode({
    ...     'Conditions': {'ConditionName': {'Fn::Equals': [1, 2]}},
    ...     'Resources': {'SomeResource': {'Condition': 'ConditionName', 'Type': 'AWS::Lambda::Function'}}
    ...     }, 'us-east-1'), sort_keys=True))
    {"Conditions": {"ConditionName": false}, "Resources": {}}
    >>> print(json.dumps(_explode({
    ...     'Conditions': {'ConditionName': {'Fn::Equals': [1, 2]}},
    ...     'Resources': {'SomeResource': {'Attribute': {'Fn::If': ['ConditionName', '1', {'Ref': 'AWS::NoValue'}]}, 'Type': 'AWS::Lambda::Function'}}
    ...     }, 'us-east-1'), sort_keys=True))
    {"Conditions": {"ConditionName": false}, "Resources": {"SomeResource": {"Type": "AWS::Lambda::Function"}}}
    >>> print(json.dumps(_explode({
    ...     'Conditions': {'ConditionName': {'Fn::Equals': [{'Ref': 'SomeBucket'}, 'SomeBucketName']}},
    ...     'Resources':
    ...         {'SomeBucket': {'Properties': {'BucketName': 'SomeBucketName'}, 'Type': 'AWS::S3::Bucket'},
    ...          'SomeResource': {'Attribute': {'Fn::If': ['ConditionName', '1', '2']}, 'Type': 'AWS::Lambda::Function'}}
    ...     }, 'us-east-1'), sort_keys=True, indent=4))
    {
        "Conditions": {
            "ConditionName": true
        },
        "Resources": {
            "SomeBucket": {
                "Properties": {
                    "BucketName": "SomeBucketName"
                },
                "Type": "AWS::S3::Bucket"
            },
            "SomeResource": {
                "Attribute": "1",
                "Type": "AWS::Lambda::Function"
            }
        }
    }
    """
    if current is None:
        current = root
        _explode(root, default_region, root)
        _cleanup(root)
        return root

    # object
    if isinstance(current, dict):
        if '_exploded' in current:
            return
        current['_exploded'] = True

        # explode children first
        for key, value in current.items():
            _exploded(root, current, key, default_region)

        condition_name = current.get('Condition')
        if condition_name:
            # condition
            if not conditions.evaluate(root, condition_name, default_region):
                return DELETE
        elif len(current) == 2: # including '_exploded'
            # possibly a condition
            key, value = next((key, value) for key, value in current.items() if key != '_exploded')
            try:
                return functions.evaluate(root, key, value, default_region)
            except KeyError as e:
                if e.args != (key,):
                    raise
                # not an intrinsic function
            try:
                return conditions.evaluate(root, {key: value}, default_region)
            except KeyError as e:
                if e.args != (key,):
                    raise
                # not a condition
    # array
    elif isinstance(current, list):
        for index, value in enumerate(current):
            _exploded(root, current, index, default_region)

def _cleanup(current):
    if isinstance(current, dict):
        if '_exploded' in current:
            del current['_exploded']
        for key, value in list(current.items()):
            if value is DELETE:
                del current[key]
            else:
                _cleanup(value)
    elif isinstance(current, list):
        deleted = 0
        for index, value in enumerate(list(current)):
            if value is DELETE:
                del current[index - deleted]
                deleted += 1
            else:
                _cleanup(value)

def _exploded(root, collection, key, default_region):
    if collection[key] is None:
        return None
    exploded = _explode(root, default_region, collection[key])
    if exploded is not None:
        collection[key] = exploded
    return collection[key]

from aws_parsecf import conditions
from aws_parsecf import functions
