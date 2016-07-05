import pytest
from awsshell.wizard import Environment, Wizard


@pytest.fixture
def env():
    env = Environment()
    env.store('env_var', {'epic': 'nice'})
    return env


def test_environment_retrieve_and_store(env):
    # Test that the env can retrieve keys via jmespath queries
    assert env.retrieve('env_var') == {'epic': 'nice'}
    assert env.retrieve('env_var.epic') == 'nice'


def test_environment_to_string(env):
    # Test that the env is properly converted into a formatted string
    display_str = '{\n    "env_var": {\n        "epic": "nice"\n    }\n}'
    assert str(env) == display_str


def test_resolve_parameters():
    # Test that env paramaters can be resolved for each key
    env = Environment()
    env.store('Epic', 'Nice')
    env.store('Test', {'k': 'v'})
    keys = {'a': 'Epic', 'b': 'Test.k'}
    resolved = env.resolve_parameters(keys)
    assert resolved == {'a': 'Nice', 'b': 'v'}


@pytest.fixture
def wizard_spec():
    return {
        'StartStage': 'TestStage',
        'Stages': [
            {
                'Name': 'TestStage',
                'Prompt': 'Prompting',
                'Retrieval': {
                    'Type': 'Static',
                    'Resource': [
                        {'Option': 'One', 'Stage': 'StageOne'},
                        {'Option': 'Two', 'Stage': 'StageTwo'}
                    ]
                },
                'Resolution': {'Path': 'Stage', 'Key': 'CreationType'},
                'NextStage': {'Type': 'Variable', 'Name': 'CreationType'}
            }
        ]
    }


def test_from_spec(wizard_spec):
    # Test that the spec is translated to the correct attrs
    wizard = Wizard(wizard_spec)
    stage_spec = wizard_spec['Stages'][0]
    stage = wizard.stages['TestStage']
    assert stage.prompt == 'Prompting'
    assert stage.name == 'TestStage'
    assert stage.retrieval == stage_spec['Retrieval']
    assert stage.next_stage == stage_spec['NextStage']
    assert stage.resolution == stage_spec['Resolution']
    assert not stage.interaction


def test_static_retrieval(wizard_spec):
    # Test that static retrieval reads the data from the spec and resolves into
    # the wizard's environment under the correct key
    wizard_spec['Stages'][0]['Resolution'] = {'Key': 'CreationType'}
    wizard = Wizard(wizard_spec)
    stage = wizard.stages['TestStage']
    stage.execute()
    assert stage.retrieval['Resource'] == wizard.env.retrieve('CreationType')


def test_static_retrieval_with_query(wizard_spec):
    # Test that static retrieval reads the data and can apply a JMESpath query
    wizard_spec['Stages'][0]['Retrieval']['Path'] = '[0].Stage'
    wizard_spec['Stages'][0]['Resolution'] = {'Key': 'CreationType'}
    wizard = Wizard(wizard_spec)
    stage = wizard.stages['TestStage']
    stage.execute()
    assert wizard.env.retrieve('CreationType') == 'StageOne'


def test_next_stage_resolution(wizard_spec):
    # Test that the stage can resolve the next stage from env
    wizard_spec['Stages'][0]['Retrieval']['Path'] = '[0]'
    wizard = Wizard(wizard_spec)
    stage = wizard.stages['TestStage']
    stage.execute()
    assert stage.get_next_stage() == 'StageOne'


def test_next_stage_static(wizard_spec):
    # Test that the stage can resolve static next stage
    wizard_spec['Stages'][0]['NextStage'] = \
        {'Type': 'Name', 'Name': 'NextStageName'}
    wizard = Wizard(wizard_spec)
    stage = wizard.stages['TestStage']
    stage.execute()
    assert stage.get_next_stage() == 'NextStageName'
