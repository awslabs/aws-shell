import six
import sys
import copy
import logging
import jmespath

import botocore.session
from botocore import xform_name
from botocore.exceptions import BotoCoreError, ClientError

from awsshell.resource import index
from awsshell.utils import force_unicode, format_json
from awsshell.selectmenu import select_prompt
from awsshell.interaction import InteractionLoader, InteractionException

from prompt_toolkit.shortcuts import confirm


LOG = logging.getLogger(__name__)


class ParamCoercion(object):
    """This class coerces string parameters into the correct type.

    By default this converts strings to numerical values if the input
    parameters model indicates that the field should be a number. This is to
    compensate for the fact that values taken in from prompts will always be
    strings and avoids having to create specific interactions for simple
    conversions or having to specify the type in the wizard specification.
    """

    _DEFAULT_DICT = {
        'integer': int,
        'float': float,
        'double': float,
        'long': int
    }

    def __init__(self, type_dict=_DEFAULT_DICT):
        """Initialize a ParamCoercion object.

        :type type_dict: dict
        :param type_dict: (Optional) A dictionary of converstions. Keys are
        strings representing the shape type name and the values are callables
        that given a string will return an instance of an appropriate type for
        that shape type. Defaults to only coerce numbers.
        """
        self._type_dict = type_dict

    def coerce(self, params, shape):
        """Coerce the params according to the given shape.

        :type params: dict
        :param params: The parameters to be given to an operation call.

        :type shape: :class:`botocore.model.Shape`
        :param shape: The input shape for the desired operation.

        :rtype: dict
        :return: The coerced version of the params.
        """
        name = shape.type_name
        if isinstance(params, dict) and name == 'structure':
            return self._coerce_structure(params, shape)
        elif isinstance(params, dict) and name == 'map':
            return self._coerce_map(params, shape)
        elif isinstance(params, (list, tuple)) and name == 'list':
            return self._coerce_list(params, shape)
        elif isinstance(params, six.string_types) and name in self._type_dict:
            target_type = self._type_dict[shape.type_name]
            return self._coerce_field(params, target_type)
        return params

    def _coerce_structure(self, params, shape):
        members = shape.members
        coerced = {}
        for param in members:
            if param in params:
                coerced[param] = self.coerce(params[param], members[param])
        return coerced

    def _coerce_map(self, params, shape):
        coerced = {}
        for key, value in params.items():
            coerced_key = self.coerce(key, shape.key)
            coerced[coerced_key] = self.coerce(value, shape.value)
        return coerced

    def _coerce_list(self, list_param, shape):
        member_shape = shape.member
        coerced_list = []
        for item in list_param:
            coerced_list.append(self.coerce(item, member_shape))
        return coerced_list

    def _coerce_field(self, value, target_type):
        try:
            return target_type(value)
        except ValueError:
            return value


def stage_error_handler(error, stages, confirm=confirm, prompt=select_prompt):
    managed_errors = (
        ClientError,
        BotoCoreError,
        WizardException,
        InteractionException,
    )

    def _select_stage_prompt():
        return prompt(u'Select a Stage to return to: ', stages)

    if isinstance(error, EOFError):
        return _select_stage_prompt()
    elif isinstance(error, managed_errors):
        sys.stdout.write('{0}\n'.format(error))
        sys.stdout.flush()
        if confirm(u'Select a previous stage? (y/n) '):
            return _select_stage_prompt()
        else:
            raise KeyboardInterrupt()
    else:
        return None


class WizardException(Exception):
    """Base exception class for the Wizards."""


class WizardLoader(object):
    """This class is responsible for searching various paths to locate wizards.

    Given a wizard name it will return a wizard object representing the wizard.
    Delegates to botocore for finding and loading the JSON models.
    """

    def __init__(self, session=None, interaction_loader=None,
                 error_handler=None):
        """Initialize a wizard factory.

        :type session: :class:`botocore.session.Session`
        :param session: (Optional) The botocore session to be used when loading
        models and retrieving clients.

        :type interaction_loader:
            :class:`awsshell.interaction.InteractionLoader`
        :param interaction_loader: (Optional) The InteractionLoader to be used
        when converting Interaction models to their corresponding object.

        :type error_handler: callable
        :param error_handler: (Optional) The error handler to be used when
        executing wizards.
        """
        self._session = session
        if session is None:
            self._session = botocore.session.Session()
        self._loader = self._session.get_component('data_loader')
        self._cached_creator = index.CachedClientCreator(self._session)
        self._interaction_loader = interaction_loader
        if interaction_loader is None:
            self._interaction_loader = InteractionLoader()
        self._error_handler = error_handler
        if error_handler is None:
            self._error_handler = stage_error_handler

    def load_wizard(self, name):
        """Given a wizard's name, return an instance of that wizard.

        :type name: str
        :param name: The name of the desired wizard.

        :rtype: :class:`Wizard`
        :return: The wizard object loaded.
        """
        # TODO possible naming collisions here, always pick first for now
        # Need to discuss and specify wizard invocation
        services = self._loader.list_available_services(type_name=name)
        if len(services) == 0:
            raise WizardException('Wizard with name %s does not exist' % name)
        else:
            model = self._loader.load_service_model(services[0], name)
            return self.create_wizard(model)

    def create_wizard(self, model):
        """Given a wizard specification, return an instance of that wizard.

        :type model: dict
        :param model: The wizard specification to be used.

        :rtype: :class:`Wizard`
        :return: The wizard object created.

        :raises: :class:`WizardException`
        """
        start_stage = model.get('StartStage')
        if not start_stage:
            raise WizardException('Start stage not specified')
        env = Environment()
        stages = self._load_stages(model.get('Stages'), env)
        return Wizard(start_stage, stages, env, self._error_handler)

    def _load_stage(self, stage, env):
        stage_attrs = {
            'name': stage.get('Name'),
            'prompt': stage.get('Prompt'),
            'retrieval': stage.get('Retrieval'),
            'next_stage': stage.get('NextStage'),
            'resolution': stage.get('Resolution'),
            'interaction': stage.get('Interaction'),
        }
        creator = self._cached_creator
        interaction = self._interaction_loader
        return Stage(env, creator, interaction, self, **stage_attrs)

    def _load_stages(self, stages, env):
        return [self._load_stage(stage, env) for stage in stages]


class Wizard(object):
    """Main wizard object. Contains main wizard driving logic."""

    def __init__(self, start_stage, stages, environment, error_handler):
        """Construct a new Wizard.

        :type start_stage: str
        :param start_stage: The name of the starting stage for the wizard.

        :type stages: list of :class:`Stage`
        :param stages: A list of stage objects for this wizard.

        :type environment: :class:`Environment`
        :param environmet: The environment for the wizard and stages

        :type error_handler: callable
        :param error_handler: A function that given an error and list of stages
        can potentially determine the stage to recover to. This function should
        return a tuple being (stage_name, index).
        """
        assert callable(error_handler)

        self.env = environment
        self.start_stage = start_stage
        self._load_stages(stages)
        self._stage_history = []
        self._error_handler = error_handler

    def _load_stages(self, stages):
        """Load the stages dictionary from the given list of stage objects.

        :type stages: list of :class:`Stage`
        :param stages: A list of stage models to be inserted into the map.
        """
        self.stages = {}
        for stage in stages:
            self.stages[stage.name] = stage

    def execute(self):
        """Run the wizard. Execute Stages until a final stage is reached.

        :raises: :class:`WizardException`
        """
        current_stage = self.start_stage
        while current_stage:
            stage = self.stages.get(current_stage)
            if not stage:
                raise WizardException('Stage not found: %s' % current_stage)
            try:
                self._push_stage(stage)
                stage_data = stage.execute()
                current_stage = stage.get_next_stage()
                if current_stage is None:
                    return stage_data
            except Exception as err:
                stages = [s.name for (s, _) in self._stage_history]
                recovery = self._error_handler(err, stages)
                if recovery is None:
                    raise
                (stage, index) = recovery
                self._pop_stages(index)
                current_stage = stage

    def _push_stage(self, stage):
        self._stage_history.append((stage, copy.deepcopy(self.env)))

    def _pop_stages(self, stage_index):
        self.env.update(self._stage_history[stage_index][1])
        self._stage_history = self._stage_history[:stage_index]


class Stage(object):
    """The Stage object. Contains logic to run all steps of the stage."""

    def __init__(self, env, creator, interaction_loader, wizard_loader,
                 name=None, prompt=None, retrieval=None, next_stage=None,
                 resolution=None, interaction=None):
        """Construct a new Stage object.

        :type env: :class:`Environment`
        :param env: The environment this stage is based in.

        :type creator: :class:`CachedClientCreator`
        :param creator: A botocore client creator that supports caching.

        :type interaction_loader: :class:`InteractionLoader`
        :param interaction_loader: The Interaction loader to be used when
        performing interactions.

        :type wizard_loader: :class:`WizardLoader`
        :param wizard_loader: The Wizard Loader to be used when a stage needs
        to delegate to a sub-wizard.

        :type name: str
        :param name: A unique identifier for the stage.

        :type prompt: str
        :param prompt: A simple message on the overall goal of the stage.

        :type retrieval: dict
        :param retrieval: The source of data for this stage.

        :type next_stage: dict
        :param next_stage: Describes what stage comes after this one.

        :type resolution: dict
        :param resolution: Describes what data to store in the environment.

        :type interaction: dict
        :param interaction: Describes what type of screen is to be used for
        interaction.
        """
        self._env = env
        self._cached_creator = creator
        self._wizard_loader = wizard_loader
        self._interaction_loader = interaction_loader
        self.name = name
        self.prompt = prompt
        self.retrieval = retrieval
        self.next_stage = next_stage
        self.resolution = resolution
        self.interaction = interaction

    def _handle_static_retrieval(self):
        return self.retrieval.get('Resource')

    def _handle_request_retrieval(self):
        req = self.retrieval['Resource']
        # get client from wizard's cache
        client = self._cached_creator.create_client(req['Service'])
        operation_name = xform_name(req['Operation'])
        # get any parameters
        parameters = req.get('Parameters', {})
        env_parameters = \
            self._env.resolve_parameters(req.get('EnvParameters', {}))
        # union of parameters and env_parameters, conflicts favor env params
        parameters = dict(parameters, **env_parameters)
        model = client.meta.service_model.operation_model(req['Operation'])
        parameters = ParamCoercion().coerce(parameters, model.input_shape)
        # if the operation supports pagination, load all results upfront
        if client.can_paginate(operation_name):
            # get paginator and create iterator
            paginator = client.get_paginator(operation_name)
            page_iterator = paginator.paginate(**parameters)
            # scroll through all pages combining them
            return page_iterator.build_full_result()
        else:
            # get the operation from the client
            operation = getattr(client, operation_name)
            # execute operation passing all parameters
            return operation(**parameters)

    def _handle_wizard_delegation(self):
        wizard_name = self.retrieval['Resource']
        wizard = self._wizard_loader.load_wizard(wizard_name)
        return wizard.execute()

    def _handle_retrieval(self):
        # In case of no retrieval, empty dict
        if not self.retrieval:
            return {}
        elif self.retrieval['Type'] == 'Static':
            data = self._handle_static_retrieval()
        elif self.retrieval['Type'] == 'Request':
            data = self._handle_request_retrieval()
        elif self.retrieval['Type'] == 'Wizard':
            data = self._handle_wizard_delegation()
        # Apply JMESPath query if given
        if self.retrieval.get('Path'):
            data = jmespath.search(self.retrieval['Path'], data)

        return data

    def _handle_interaction(self, data):
        # if no interaction step, just forward data
        if self.interaction is None:
            return data
        else:
            creator = self._interaction_loader.create
            interaction = creator(self.interaction, self.prompt)
            return interaction.execute(force_unicode(data))

    def _handle_resolution(self, data):
        if self.resolution:
            if self.resolution.get('Path'):
                data = jmespath.search(self.resolution['Path'], data)
            self._env.store(self.resolution['Key'], data)
        return data

    def get_next_stage(self):
        """Resolve the next stage name for the stage after this one.

        :rtype: str
        :return: The name of the next stage.
        """
        if not self.next_stage:
            return None
        elif self.next_stage['Type'] == 'Name':
            return self.next_stage['Name']
        elif self.next_stage['Type'] == 'Variable':
            return self._env.retrieve(self.next_stage['Name'])

    def execute(self):
        """Execute all three steps in the stage if they are present.

        1) Perform Retrieval.
        2) Perform Interaction on retrieved data.
        3) Perform Resolution to store data in the environment.
        """
        retrieved_options = self._handle_retrieval()
        selected_data = self._handle_interaction(retrieved_options)
        resolved_data = self._handle_resolution(selected_data)
        return resolved_data


class Environment(object):
    """Store vars into a dict and retrives them with JMESPath queries."""

    def __init__(self):
        self._variables = {}

    def __str__(self):
        return format_json(self._variables)

    def update(self, environment):
        assert isinstance(environment, Environment)
        self._variables = environment._variables

    def store(self, key, val):
        """Store a variable under the given key.

        :type key: str
        :param key: The key to store the value as.

        :type val: object
        :param val: The value to store into the environment.
        """
        self._variables[key] = val

    def retrieve(self, path):
        """Retrieve the variable corresponding to the given JMESPath query.

        :type path: str
        :param path: The JMESPath query to be used when locating the variable.
        """
        return jmespath.search(path, self._variables)

    def resolve_parameters(self, keys):
        """Resolve all keys in the given keys dict.

        Expects all values in the keys dict to be JMESPath queries to be used
        when retrieving from the environment. Interpolates all values from
        their path to the actual value stored in the environment.

        :type keys: dict
        :param keys: A dict of keys to paths that need to be resolved.

        :rtype: dict
        :return: The dict of with all of the paths resolved to their values.
        """
        resolved_dict = {}
        for key in keys:
            retrieved = self.retrieve(keys[key])
            if retrieved is not None:
                resolved_dict[key] = retrieved
            else:
                LOG.debug("Query failed (%s), dropped key: %s", keys[key], key)

        return resolved_dict
