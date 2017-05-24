from aws_parsecf.parser import Parser
import boto3
import json
import yaml

def load_json(stream, default_region=boto3.Session().region_name):
    return _load(json.load(stream), default_region)

def loads_json(string, default_region=boto3.Session().region_name):
    return _load(json.loads(string), default_region)

def load_yaml(stream_or_string, default_region=boto3.Session().region_name):
    return _load(yaml.load(stream_or_string), default_region)

def _load(root, default_region):
    """
    >>> import json

    >>> print(json.dumps(_load({
    ...     'Conditions': {'ConditionName': {'Fn::Equals': [1, 2]}},
    ...     'Resources': {'SomeResource': {'Condition': 'ConditionName', 'Type': 'AWS::Lambda::Function'}}
    ...     }, 'us-east-1'), sort_keys=True))
    {"Conditions": {"ConditionName": false}, "Resources": {}}
    >>> print(json.dumps(_load({
    ...     'Conditions': {'ConditionName': {'Fn::Equals': [1, 1]}},
    ...     'Resources': {'SomeResource': {'Condition': 'ConditionName', 'Type': 'AWS::Lambda::Function'}}
    ...     }, 'us-east-1'), sort_keys=True))
    {"Conditions": {"ConditionName": true}, "Resources": {"SomeResource": {"Condition": "ConditionName", "Type": "AWS::Lambda::Function"}}}
    >>> print(json.dumps(_load({
    ...     'Resources': {'SomeResource': {'Condition': {'DateGreaterThan': {'aws:CurrentTime': '2013-12-15T12:00:00Z'}, 'Type': 'AWS::IAM::Role'}}}
    ...     }, 'us-east-1'), sort_keys=True))
    {"Resources": {"SomeResource": {"Condition": {"DateGreaterThan": {"aws:CurrentTime": "2013-12-15T12:00:00Z"}, "Type": "AWS::IAM::Role"}}}}
    >>> print(json.dumps(_load({
    ...     'Conditions': {'ConditionName': {'Fn::Equals': [1, 2]}},
    ...     'Resources': {'SomeResource': {'Attribute': {'Fn::If': ['ConditionName', '1', {'Ref': 'AWS::NoValue'}]}, 'Type': 'AWS::Lambda::Function'}}
    ...     }, 'us-east-1'), sort_keys=True))
    {"Conditions": {"ConditionName": false}, "Resources": {"SomeResource": {"Type": "AWS::Lambda::Function"}}}
    >>> print(json.dumps(_load({
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

    if not default_region:
        raise TypeError("No default region in aws configuration, please specify one (with `aws configure` or `default_region=`)")
    parser = Parser(root, default_region)
    parser.explode(root)
    parser.cleanup(root)
    return root

