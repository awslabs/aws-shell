import json
import jmespath

import botocore.session
from botocore import xform_name

from awsshell.resource import index
from awsshell.interaction import InteractionLoader


class WizardException(Exception):
    """Base exception class for the Wizards."""


class WizardLoader(object):
    """This class is responsible for searching various paths to locate wizards.

    Given a wizard name it will return a wizard object representing the wizard.
    Delegates to botocore for finding and loading the JSON models.
    """

    def __init__(self, session=None, interaction_loader=None):
        """Initialize a wizard factory.

        :type session: :class:`botocore.session.Session`
        :param session: (Optional) The botocore session to be used when loading
        models and retrieving clients.

        :type interaction_loader:
            :class:`awsshell.interaction.InteractionLoader`
        :param interaction_loader: (Optional) The InteractionLoader to be used
        when converting Interaction models to their corresponding object.
        """
        self._session = session
        if session is None:
            self._session = botocore.session.Session()
        self._loader = self._session.get_component('data_loader')
        self._cached_creator = index.CachedClientCreator(self._session)
        self._interaction_loader = interaction_loader
        if interaction_loader is None:
            self._interaction_loader = InteractionLoader()

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
        return Wizard(start_stage, stages, env)

    def _load_stages(self, stages, env):
        def load_stage(stage):
            stage_attrs = {
                'name': stage.get('Name'),
                'prompt': stage.get('Prompt'),
                'retrieval': stage.get('Retrieval'),
                'next_stage': stage.get('NextStage'),
                'resolution': stage.get('Resolution'),
                'interaction': stage.get('Interaction'),
            }
            creator = self._cached_creator
            loader = self._interaction_loader
            return Stage(env, creator, loader, **stage_attrs)
        return [load_stage(stage) for stage in stages]


class Wizard(object):
    """Main wizard object. Contains main wizard driving logic."""

    def __init__(self, start_stage, stages, environment):
        """Construct a new Wizard.

        :type start_stage: str
        :param start_stage: The name of the starting stage for the wizard.

        :type stages: list of :class:`Stage`
        :param stages: A list of stage objects for this wizard.

        :type environment: :class:`Environment`
        :param environmet: The environment for the wizard and stages
        """
        self.env = environment
        self.start_stage = start_stage
        self._load_stages(stages)

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
            stage.execute()
            current_stage = stage.get_next_stage()


class Stage(object):
    """The Stage object. Contains logic to run all steps of the stage."""

    def __init__(self, env, creator, interaction_loader, name=None,
                 prompt=None, retrieval=None, next_stage=None, resolution=None,
                 interaction=None):
        """Construct a new Stage object.

        :type env: :class:`Environment`
        :param env: The environment this stage is based in.

        :type creator: :class:`CachedClientCreator`
        :param creator: A botocore client creator that supports caching.

        :type interaction_loader: :class:`InteractionLoader`
        :param interaction_loader: The Interaction loader to be used when
        performing interactions.

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
        # get the operation from the client
        operation = getattr(client, xform_name(req['Operation']))
        # get any parameters
        parameters = req.get('Parameters', {})
        env_parameters = \
            self._env.resolve_parameters(req.get('EnvParameters', {}))
        # union of parameters and env_parameters, conflicts favor env_params
        parameters = dict(parameters, **env_parameters)
        # execute operation passing all parameters
        return operation(**parameters)

    def _handle_retrieval(self):
        # In case of no retrieval, empty dict
        if not self.retrieval:
            return {}
        elif self.retrieval['Type'] == 'Static':
            data = self._handle_static_retrieval()
        elif self.retrieval['Type'] == 'Request':
            data = self._handle_request_retrieval()
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
            return interaction.execute(data)

    def _handle_resolution(self, data):
        if self.resolution:
            if self.resolution.get('Path'):
                data = jmespath.search(self.resolution['Path'], data)
            self._env.store(self.resolution['Key'], data)

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
        self._handle_resolution(selected_data)


class Environment(object):
    """Store vars into a dict and retrives them with JMESPath queries."""

    def __init__(self):
        self._variables = {}

    def __str__(self):
        return json.dumps(self._variables, indent=4, sort_keys=True)

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
        for key in keys:
            keys[key] = self.retrieve(keys[key])
        return keys
