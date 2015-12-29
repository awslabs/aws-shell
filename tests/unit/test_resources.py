"""Index and retrive information from the resource JSON."""
import pytest
import mock

from botocore.exceptions import NoRegionError

from awsshell.resource import index


@pytest.fixture
def describer_creator():
    class FakeDescriberCreator(object):
        SERVICES = ['ec2']

        def services_with_completions(self):
            return self.SERVICES

    return FakeDescriberCreator()


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
    q = index.CompleterDescriber(built_index)
    result = q.describe_autocomplete(
        'dynamodb', 'DeleteTable', 'TableName')
    assert result.service == 'dynamodb'
    assert result.operation == 'ListTables'
    assert result.params == {}
    assert result.path == 'TableNames[]'


def test_cached_client_creator_returns_same_instance():
    class FakeSession(object):
        def create_client(self, service_name):
            return object()

    cached_creator = index.CachedClientCreator(FakeSession())
    ec2 = cached_creator.create_client('ec2')
    s3 = cached_creator.create_client('s3')
    assert ec2 != s3
    # However, asking for a client we've already created
    # should return the exact same instance.
    assert cached_creator.create_client('ec2') == ec2


def test_can_create_service_completers_from_cache():
    class FakeDescriberCreator(object):
        def load_service_model(self, service_name, type_name):
            assert type_name == 'completions-1'
            return "fake_completions_for_%s" % service_name

        def services_with_completions(self):
            return []

    loader = FakeDescriberCreator()
    factory = index.CompleterDescriberCreator(loader)
    result = factory.create_completer_query('ec2')
    assert isinstance(result, index.CompleterDescriber)
    assert factory.create_completer_query('ec2') == result


def test_empty_results_returned_when_no_completion_data_exists(describer_creator):
    describer_creator.SERVICES = []

    completer = index.ServerSideCompleter(
        client_creator=None,
        describer_creator=describer_creator,
    )
    assert completer.retrieve_candidate_values(
        'ec2', 'run-instances', 'ImageId') == []


def test_no_completions_when_cant_create_client(describer_creator):
    client_creator = mock.Mock(spec=index.CachedClientCreator)
    # This is raised when you don't have a region configured via config file
    # env var or manually via a session.
    client_creator.create_client.side_effect = NoRegionError()
    completer = index.ServerSideCompleter(
        client_creator=client_creator,
        describer_creator=describer_creator)

    assert completer.retrieve_candidate_values(
        'ec2', 'foo', 'Bar') == []


def test_no_completions_returned_on_unknown_operation(describer_creator):
    client = mock.Mock()
    client_creator = mock.Mock(spec=index.CachedClientCreator)
    client_creator.create_client.return_value = client

    client.meta.method_to_api_mapping = {
        'describe_foo': 'DescribeFoo'
    }

    completer = index.ServerSideCompleter(
        client_creator=client_creator,
        describer_creator=describer_creator)

    assert completer.retrieve_candidate_values(
        'ec2', 'not_describe_foo', 'Bar') == []
