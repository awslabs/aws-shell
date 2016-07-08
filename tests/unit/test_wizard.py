import mock
import pytest
from awsshell.wizard import Environment, WizardLoader, WizardException


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
def loader(wizard_spec):
    session = mock.Mock()
    return WizardLoader(session)


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
            },
            {
                'Name': 'StageTwo',
                'Prompt': 'Prompting Too'
            }
        ]
    }


@pytest.fixture
def wizard_spec_request():
    return {
        'StartStage': 'TestStage',
        'Stages': [
            {
                'Name': 'TestStage',
                'Prompt': 'Prompting',
                'Retrieval': {
                    'Type': 'Static',
                    'Resource': {'ApiName': 'new api name'}
                },
                'Resolution': {'Path': 'ApiName', 'Key': 'ApiName'},
                'NextStage': {'Type': 'Name', 'Name': 'StageTwo'}
            },
            {
                'Name': 'StageTwo',
                'Prompt': 'Prompting',
                'Retrieval': {
                    'Type': 'Request',
                    'Resource': {
                        'Service': 'apigateway',
                        'Operation':
                        'CreateRestApi',
                        'Parameters': {'param': 'value'},
                        'EnvParameters': {'name': 'ApiName'}
                    }
                },
                'Resolution': {'Path': 'id', 'Key': 'CreatedId'},
                'NextStage': {'Type': 'Variable', 'Name': 'CreationType'}
            }
        ]
    }


def test_from_spec(wizard_spec, loader):
    # Test that the spec is translated to the correct attrs
    wizard = loader.create_wizard(wizard_spec)
    stage_spec = wizard_spec['Stages'][0]
    stage = wizard.stages['TestStage']
    assert stage.prompt == 'Prompting'
    assert stage.name == 'TestStage'
    assert stage.retrieval == stage_spec['Retrieval']
    assert stage.next_stage == stage_spec['NextStage']
    assert stage.resolution == stage_spec['Resolution']
    assert not stage.interaction


def test_static_retrieval(wizard_spec, loader):
    # Test that static retrieval reads the data from the spec and resolves into
    # the wizard's environment under the correct key
    wizard_spec['Stages'][0]['Resolution'] = {'Key': 'CreationType'}
    wizard = loader.create_wizard(wizard_spec)
    stage = wizard.stages['TestStage']
    stage.execute()
    assert stage.retrieval['Resource'] == wizard.env.retrieve('CreationType')


def test_static_retrieval_with_query(wizard_spec, loader):
    # Test that static retrieval reads the data and can apply a JMESpath query
    wizard_spec['Stages'][0]['Retrieval']['Path'] = '[0].Stage'
    wizard_spec['Stages'][0]['Resolution'] = {'Key': 'CreationType'}
    wizard = loader.create_wizard(wizard_spec)
    stage = wizard.stages['TestStage']
    stage.execute()
    assert wizard.env.retrieve('CreationType') == 'StageOne'


def test_request_retrieval(wizard_spec_request):
    # Tests that retrieval requests are parsed and call the correct operation
    mock_session = mock.Mock()
    mock_request = mock_session.create_client.return_value.create_rest_api
    mock_request.return_value = {'id': 'api id', 'name': 'random name'}

    loader = WizardLoader(mock_session)
    wizard = loader.create_wizard(wizard_spec_request)
    wizard.execute()
    mock_request.assert_called_once_with(param='value', name='new api name')


def test_next_stage_resolution(wizard_spec, loader):
    # Test that the stage can resolve the next stage from env
    wizard_spec['Stages'][0]['Retrieval']['Path'] = '[0]'
    wizard = loader.create_wizard(wizard_spec)
    stage = wizard.stages['TestStage']
    stage.execute()
    assert stage.get_next_stage() == 'StageOne'


def test_next_stage_static(wizard_spec, loader):
    # Test that the stage can resolve static next stage
    wizard_spec['Stages'][0]['NextStage'] = \
        {'Type': 'Name', 'Name': 'NextStageName'}
    wizard = loader.create_wizard(wizard_spec)
    stage = wizard.stages['TestStage']
    stage.execute()
    assert stage.get_next_stage() == 'NextStageName'


def test_basic_full_execution(wizard_spec, loader):
    # Test that the wizard can advance stages and finish a wizard
    wizard_spec['Stages'][0]['NextStage'] = \
        {'Type': 'Name', 'Name': 'StageTwo'}
    wizard_spec['Stages'][0]['Resolution']['Path'] = '[0].Stage'
    wizard = loader.create_wizard(wizard_spec)
    wizard.execute()
    display_str = '{\n    "CreationType": "StageOne"\n}'
    assert str(wizard.env) == display_str


def test_missing_start_stage(wizard_spec, loader):
    # Test that the loader throws an error if the spec is missing start stage
    wizard_spec['StartStage'] = None
    with pytest.raises(WizardException) as we:
        loader.create_wizard(wizard_spec)
    assert 'Start stage not specified' in str(we.value)


def test_missing_stage(wizard_spec, loader):
    # Test that the loader throws an error if the spec is missing start stage
    wizard_spec['Stages'][0]['NextStage'] = \
        {'Type': 'Name', 'Name': 'ImpendingDoom'}
    wizard = loader.create_wizard(wizard_spec)
    with pytest.raises(WizardException) as we:
        wizard.execute()
    assert 'Stage not found: ImpendingDoom' in str(we.value)


def test_wizard_loader(wizard_spec):
    # Tests that the wizard loader can access models via the botocore loader
    mock_session = mock.Mock()
    mock_loader = mock_session.get_component.return_value
    mock_loader.list_available_services.return_value = ['wizards']
    mock_loader.load_service_model.return_value = wizard_spec
    loader = WizardLoader(mock_session)

    w1 = loader.load_wizard('wizname')
    w2 = loader.create_wizard(wizard_spec)

    mock_session.get_component.assert_called_once_with('data_loader')
    mock_list = mock_loader.list_available_services
    mock_model = mock_loader.load_service_model
    mock_list.assert_called_once_with(type_name='wizname')
    mock_model.assert_called_once_with('wizards', 'wizname')
    assert w1.start_stage == w2.start_stage


def test_wizard_loader_no_session(wizard_spec, loader):
    test_loader = WizardLoader()
    w1 = test_loader.create_wizard(wizard_spec)
    w2 = loader.create_wizard(wizard_spec)
    assert w1.start_stage == w2.start_stage
