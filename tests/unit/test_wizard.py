import unittest
from awsshell.wizard import Wizard
from awsshell.wizard import Environment
from awsshell.wizard import Stage


class EnvironmentTest(unittest.TestCase):

    # Set up a sample environment
    def setUp(self):
        self.var = {'epic': 'nice'}
        self.env = Environment()
        self.env.store('env_var', self.var)

    # Test that the environment properly stores the given var
    def test_environment_store(self):
        self.assertEqual(self.env._variables.get('env_var'), self.var)

    # Test that the env can retrieve keys via jmespath queries
    def test_environment_retrieve(self):
        self.assertEqual(self.env.retrieve('env_var'), self.var)
        self.assertEqual(self.env.retrieve('env_var.epic'), 'nice')


class StageTest(unittest.TestCase):

    # Set up a sample stage
    def setUp(self):
        self.wiz = Wizard()
        self.retrieval = {
            'Type': 'Static',
            'Resource': [
                {'Option': 'Create new Api', 'Stage': 'CreateApi'},
                {
                    'Option': 'Generate new Api from swagger spec file',
                    'Stage': 'NewSwaggerApi'
                }
            ]
        }
        self.interaction = {'ScreenType': 'SimpleSelect'},
        self.resolution = {'Path': 'Stage', 'Key': 'CreationType'}
        self.next_stage = {'Type': 'Variable', 'Name': 'CreationType'}
        self.stage_spec = {
            'Name': 'ApiSourceSwitch',
            'Prompt': 'Prompting',
            'Retrieval': self.retrieval,
            'Interaction': self.interaction,
            'Resolution': self.resolution,
            'NextStage': self.next_stage
        }

    # Test that the spec is translated to the correct attrs
    def test_from_spec(self):
        test_env = Environment()
        stage = Stage(self.stage_spec, test_env)
        self.assertEqual(stage.name, 'ApiSourceSwitch')
        self.assertEqual(stage.prompt, 'Prompting')
        self.assertEqual(stage.retrieval, self.retrieval)
        self.assertEqual(stage.interaction, self.interaction)
        self.assertEqual(stage.resolution, self.resolution)
        self.assertEqual(stage.next_stage, self.next_stage)

    # Test that static retrieval reads the data straight from the spec
    def test_static_retrieval(self):
        test_env = Environment()
        stage = Stage(self.stage_spec, test_env)
        ret = stage._handle_retrieval()
        self.assertEqual(ret, self.retrieval['Resource'])

    # Test that resolution properly puts the resolved value into the env
    def test_handle_resolution(self):
        test_env = Environment()
        stage = Stage(self.stage_spec, test_env)
        data = {'Stage': 'EpicNice'}
        stage._handle_resolution(data)
        self.assertEqual(test_env.retrieve('CreationType'), 'EpicNice')

    # Test that env paramaters can be resolved for the stage
    def test_resolve_parameters(self):
        test_env = Environment()
        test_env.store('Epic', 'Nice')
        test_env.store('Test', {'k': 'v'})
        keys = {'a': 'Epic', 'b': 'Test.k'}
        stage = Stage(self.stage_spec, test_env)
        resolved = stage._resolve_parameters(keys)
        self.assertEqual(resolved, {'a': 'Nice', 'b': 'v'})
