"""Index and retrive information from the resource JSON."""
import jmespath


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


def main():
    import sys
    import json
    builder = ResourceIndexBuilder()
    index = builder.build_index(json.load(open(sys.argv[1])))
    print json.dumps(index, indent=2)


if __name__ == '__main__':
    main()
