"""Index and retrive information from the resource JSON.

The classes are organized as follows:

* ResourceIndexBuilder - Takes a boto3 resource and converts into the
  index format we need to do server side completions.
* CompleterQuery - Takes the index from ResourceIndexBuilder and looks
  up how to perform the autocompletion.  Note that this class does
  *not* actually do the autocompletion.  It merely tells you how
  you _would_ do the autocompletion if you made the appropriate
  service calls.
* ServerSideCompleter - The thing that does the actual autocompletion.
  You tell it the command/operation/param you're on, and it will
  return a list of completions for you.

"""
import logging
from collections import namedtuple

import jmespath
from botocore import xform_name

LOG = logging.getLogger(__name__)

# service - The name of the AWS service
# operation - The name of the AWS operation
# params - A dict of params to send in the request (not implemented yet)
# path - A JMESPath expression to select the expected elements.
ServerCompletion = namedtuple('ServerCompletion',
                              ['service', 'operation', 'params', 'path'])


def extract_field_from_jmespath(expression):
    result = jmespath.compile(expression)
    current = result.parsed
    while current['children']:
        current = current['children'][0]
    if current['type'] == 'field':
        return current['value']


class ResourceIndexBuilder(object):
    def __init__(self):
        pass

    def build_index(self, resource_data):
        # First we need to go through the 'resources'
        # key and map all of its actions back to the
        # resource name.
        index = {
            'operations': {},
            'resources': {},
        }
        service = resource_data['service']
        if 'hasMany' in service:
            for has_many_name, model in service['hasMany'].items():
                resource_name = model['resource']['type']
                for identifier in model['resource']['identifiers']:
                    first_identifier = model['resource']['identifiers'][0]
                    index['resources'][resource_name] = {
                        'operation': model['request']['operation'],
                        # TODO: map all the identifiers.
                        # We're only taking the first one for now.
                        'resourceIdentifier': {
                            first_identifier['target']: first_identifier['path']
                        }
                    }
        for resource_name, model in resource_data['resources'].items():
            if resource_name not in index['resources']:
                continue
            if 'actions' in model:
                resource_actions = model['actions']
                for action_name, action_model in resource_actions.items():
                    op_name = action_model['request']['operation']
                    current = {}
                    index['operations'][op_name] = current
                    for param in action_model['request']['params']:
                        if param['source'] == 'identifier':
                            field_name = extract_field_from_jmespath(
                                param['target'])
                            current[field_name] = {
                                'resourceName': resource_name,
                                'resourceIdentifier': param['name'],
                            }
        return index


class CompleterQuery(object):
    """Describes how to autocomplete a resource."""
    def __init__(self, resource_index):
        self._index = resource_index

    def describe_autocomplete(self, service, operation, param):
        """

        :type service: str
        :param service: The AWS service name.

        :type operation: str
        :param operation: The AWS operation name.

        :type param: str
        :param param: The name of the parameter being completed.  This must
            match the casing in the service model (e.g. InstanceIds, not
            --instance-ids).

        :rtype: ServerCompletion
        :return: A ServerCompletion object that describes what API call to make
            in order to complete the response.

        """
        service_index = self._index[service]
        LOG.debug(service_index)
        if param not in service_index.get('operations', {}).get(operation, {}):
            LOG.debug("param not in index: %s", param)
            return None
        p = service_index['operations'][operation][param]
        resource_name = p['resourceName']
        resource_identifier = p['resourceIdentifier']

        resource_index = service_index['resources'][resource_name]
        completion_operation = resource_index['operation']
        path = resource_index['resourceIdentifier'][resource_identifier]
        return ServerCompletion(service=service, operation=completion_operation,
                                params={}, path=path)


class ServerSideCompleter(object):
    def __init__(self, session, builder):
        # session is a boto3 session.
        # It is a public attribute as it is intended to be
        # changed if the profile changes.
        self.session = session
        self._loader = session._loader
        self._builder = builder
        self._client_cache = {}
        self._completer_cache = {}

    def _get_completer_for_service(self, service_name, resource_model):
        if service_name not in self._completer_cache:
            index = self._builder.build_index(resource_model)
            cq = CompleterQuery({service_name: index})
            self._completer_cache[service_name] = cq
        return self._completer_cache[service_name]

    def _get_client(self, service_name):
        if service_name in self._client_cache:
            return self._client_cache[service_name]
        client = self.session.client(service_name)
        self._client_cache[service_name] = client
        return client

    def autocomplete(self, service, operation, param):
        # Example call:
        # service='ec2', operation='terminate-instances',
        # param='--instance-ids'.
        # We need to convert this to botocore syntax.
        # First try to load the resource model.
        LOG.debug("Called with: %s, %s, %s", service, operation, param)
        try:
            resource_model = self._loader.load_service_model(
                service, 'resources-1')
        except Exception as e:
            # No resource == no server side completion.
            return
        # Now convert operation to the name used by botocore.
        client = self._get_client(service)
        api_operation_name = client.meta.method_to_api_mapping.get(
            operation.replace('-', '_'))
        if api_operation_name is None:
            return
        # Now we need to convert the param name to the
        # casing used by the API.
        completer = self._get_completer_for_service(service,
                                                    resource_model)
        result = completer.describe_autocomplete(
            service, api_operation_name, param)
        if result is None:
            return
        # DEBUG:awsshell.resource.index:RESULTS:
            # ServerCompletion(service=u'ec2', operation=u'DescribeInstances',
            # params={}, path=u'Reservations[].Instances[].InstanceId')
        try:
            response = getattr(client, xform_name(result.operation, '_'))()
        except Exception as e:
            return
        results = jmespath.search(result.path, response)
        return results


def main():
    import sys
    import json
    builder = ResourceIndexBuilder()
    index = builder.build_index(json.load(open(sys.argv[1])))
    print json.dumps(index, indent=2)


if __name__ == '__main__':
    main()
