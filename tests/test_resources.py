"""Index and retrive information from the resource JSON."""
import pytest
from awsshell.resource import index


def test_build_from_has_many():
    resource = {
        'service': {
            'hasMany': {
                'Tables': {
                    'request': {'operation': 'ListTables'},
                    'resource': {
                        'type': 'Table',
                        'identifiers': [
                            {'target': 'Name',
                             'source': 'response',
                             'path': 'TableNames[]',
                            }
                        ]
                    }
                }
            }
        },
        'resources': {
            'Table': {
                'actions': {
                    'Delete': {
                        'request': {
                            'operation': 'DeleteTable',
                            'params': [
                                {'target': 'TableName',
                                 'source': 'identifier',
                                 'name': 'Name'},
                            ]
                        }
                    }
                }
            }
        }
    }
    builder = index.ResourceIndexBuilder()
    built_index = builder.build_index(resource)
    assert built_index == {
        'operations': {
            'DeleteTable': {
                'TableName': {
                    'resourceName': 'Table',
                    'resourceIdentifier': 'Name',
                }
            }
        },
        'resources': {
            'Table': {
                'operation': 'ListTables',
                'resourceIdentifier': {
                    'Name': 'TableNames[]',
                }
            }
        }
    }


def test_removes_jmespath_expressions_from_targets():
    resource = {
        'service': {
            'hasMany': {
                'Instances': {
                    'request': {'operation': 'DescribeInstances'},
                    'resource': {
                        'type': 'Instance',
                        'identifiers': [
                            {'target': 'Id',
                             'source': 'response',
                             'path': 'Reservations[].Instances[].InstanceId',
                            }
                        ]
                    }
                }
            }
        },
        'resources': {
            'Instance': {
                'actions': {
                    'Terminate': {
                        'request': {
                            'operation': 'TerminateInstances',
                            'params': [
                                {'target': 'InstanceIds[0]',
                                 'source': 'identifier',
                                 'name': 'Id'},
                            ]
                        }
                    }
                }
            }
        }
    }
    builder = index.ResourceIndexBuilder()
    built_index = builder.build_index(resource)
    assert built_index == {
        'operations': {
            'TerminateInstances': {
                'InstanceIds': {
                    'resourceName': 'Instance',
                    'resourceIdentifier': 'Id',
                }
            }
        },
        'resources': {
            'Instance': {
                'operation': 'DescribeInstances',
                'resourceIdentifier': {
                    'Id': 'Reservations[].Instances[].InstanceId',
                }
            }
        }
    }


def test_resource_not_included_if_no_has_many():
    # This is something we can fix, but for now the resource
    # must be in the hasMany.
    resource = {
        'service': {
            'hasMany': {}
        },
        'resources': {
            'Tag': {
                'actions': {
                    'Delete': {
                        'request': {
                            'operation': 'DeleteTags',
                            'params': [
                                {'target': 'Resources[0]',
                                 'source': 'identifier',
                                 'name': 'ResourceId'},
                            ]
                        }
                    }
                }
            }
        }
    }
    builder = index.ResourceIndexBuilder()
    built_index = builder.build_index(resource)
    # The index is empty because there was not matching
    # hasMany resource.
    assert built_index == {
        'operations': {},
        'resources': {},
    }


def test_can_complete_query():
    built_index = {
        'dynamodb': {
            'operations': {
                'DeleteTable': {
                    'TableName': {
                        'resourceName': 'Table',
                        'resourceIdentifier': 'Name',
                    }
                }
            },
            'resources': {
                'Table': {
                    'operation': 'ListTables',
                    'resourceIdentifier': {
                        'Name': 'TableNames[]',
                    }
                }
            }
        }
    }
    q = index.CompleterQuery(built_index)
    result = q.describe_autocomplete(
        'dynamodb', 'DeleteTable', 'TableName')
    assert result.service == 'dynamodb'
    assert result.operation == 'ListTables'
    assert result.params == {}
    assert result.path == 'TableNames[]'
