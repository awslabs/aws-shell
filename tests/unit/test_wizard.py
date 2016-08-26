import mock
import pytest
import botocore.session

from botocore.loaders import Loader
from botocore.session import Session
from awsshell.utils import FileReadError
from awsshell.wizard import stage_error_handler
from awsshell.interaction import InteractionException
from botocore.exceptions import ClientError, BotoCoreError
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
    mock_session = mock.Mock(spec=Session)
    mock_session.create_client.return_value.can_paginate.return_value = False
    mock_request = mock_session.create_client.return_value.create_rest_api
    mock_request.return_value = {'id': 'api id', 'name': 'random name'}

    loader = WizardLoader(mock_session)
    wizard = loader.create_wizard(wizard_spec_request)
    wizard.execute()
    mock_request.assert_called_once_with(param='value', name='new api name')


def test_request_retrieval_paginate(wizard_spec_request):
    # Tests that retrieval requests are parsed and call the correct operation
    mock_session = mock.Mock(spec=Session)
    mock_client = mock_session.create_client.return_value
    mock_client.can_paginate.return_value = True
    mock_paginator = mock_client.get_paginator.return_value
    mock_iterator = mock_paginator.paginate.return_value
    result = {'id': 'api id', 'name': 'random name'}
    mock_iterator.build_full_result.return_value = result
    paginate = mock_paginator.paginate

    loader = WizardLoader(mock_session)
    wizard = loader.create_wizard(wizard_spec_request)
    wizard.execute()
    paginate.assert_called_once_with(param='value', name='new api name')


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


def test_basic_full_execution_error(wizard_spec):
    # Test that the wizard can handle exceptions in stage execution
    session = mock.Mock()
    error_handler = mock.Mock(side_effect=[('TestStage', 0), None])
    loader = WizardLoader(session, error_handler=error_handler)
    wizard_spec['Stages'][0]['NextStage'] = \
        {'Type': 'Name', 'Name': 'StageTwo'}
    wizard_spec['Stages'][0]['Resolution']['Path'] = '[0].Stage'
    stage_three = {'Name': 'StageThree', 'Prompt': 'Text'}
    wizard = loader.create_wizard(wizard_spec)
    # force two exceptions, recover once then fail to recover
    errors = [WizardException(), TypeError()]
    wizard.stages['StageTwo'].execute = mock.Mock(side_effect=errors)
    with pytest.raises(TypeError):
        wizard.execute()
    # assert error handler was called twice
    assert error_handler.call_count == 2
    assert wizard.stages['StageTwo'].execute.call_count == 2


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


def test_wizard_loader_not_found():
    mock_session = mock.Mock()
    mock_loader = mock_session.get_component.return_value
    mock_loader.list_available_services.return_value = []
    loader = WizardLoader(mock_session)
    with pytest.raises(WizardException) as we:
        loader.load_wizard('wizname')
    assert 'Wizard with name wizname does not exist' in str(we.value)


def test_wizard_loader_no_session(wizard_spec, loader):
    # Test that the wizard loader still functions without a given session
    test_loader = WizardLoader()
    w1 = test_loader.create_wizard(wizard_spec)
    w2 = loader.create_wizard(wizard_spec)
    assert w1.start_stage == w2.start_stage


def test_wizard_basic_interaction(wizard_spec):
    # Test that the wizard calls the interaction's execute
    inter = {'ScreenType': 'SomeScreen'}
    opt = {'Option': 'Two', 'Stage': 'StageTwo'}
    data = [{'Option': 'One', 'Stage': 'StageOne'}, opt]
    i_loader = mock.Mock()
    i_loader.create.return_value.execute.return_value = opt
    wizard_spec['Stages'][0]['Interaction'] = inter
    test_loader = WizardLoader(interaction_loader=i_loader)
    wiz = test_loader.create_wizard(wizard_spec)
    wiz.execute()
    create = i_loader.create
    create.assert_called_once_with(inter, 'Prompting')
    create.return_value.execute.assert_called_once_with(data)


def test_wizard_basic_delegation(wizard_spec):
    main_spec = {
        "StartStage": "One",
        "Stages": [
            {
                "Name": "One",
                "Prompt": "stage one",
                "Retrieval": {
                    "Type": "Wizard",
                    "Resource": "SubWizard",
                    "Path": "FromSub"
                }
            }
        ]
    }
    sub_spec = {
        "StartStage": "SubOne",
        "Stages": [
            {
                "Name": "SubOne",
                "Prompt": "stage one",
                "Retrieval": {
                    "Type": "Static",
                    "Resource": {"FromSub": "Result from sub"}
                }
            }
        ]
    }

    mock_loader = mock.Mock(spec=Loader)
    mock_loader.list_available_services.return_value = ['wizards']
    mock_load_model = mock_loader.load_service_model
    mock_load_model.return_value = sub_spec

    session = botocore.session.get_session()
    session.register_component('data_loader', mock_loader)
    loader = WizardLoader(session)
    wizard = loader.create_wizard(main_spec)

    result = wizard.execute()
    mock_load_model.assert_called_once_with('wizards', 'SubWizard')
    assert result == 'Result from sub'


exceptions = [
    BotoCoreError(),
    WizardException('error'),
    InteractionException('error'),
    ClientError({'Error': {}}, 'Operation')
]


@pytest.mark.parametrize('err', exceptions)
@pytest.mark.parametrize('accept_confirm', [True, False])
def test_stage_exception_handler(err, accept_confirm):
    # Verify known exceptions will confirm retry and prompt
    confirm = mock.Mock()
    confirm.return_value = accept_confirm
    prompt = mock.Mock()
    stages = ['stage1', 'stage2']
    try:
        stage_error_handler(err, stages, confirm=confirm, prompt=prompt)
        assert accept_confirm
        assert prompt.call_count == 1
    except KeyboardInterrupt:
        assert not accept_confirm
        assert prompt.call_count == 0


def test_stage_exception_handler_eof():
    # Verify EOFError directly calls the prompt
    prompt = mock.Mock()
    confirm = mock.Mock()
    stage_error_handler(EOFError(), ['stage'], confirm=confirm, prompt=prompt)
    assert confirm.call_count == 0
    assert prompt.call_count == 1


@pytest.mark.parametrize('error_class', [FileReadError, Exception])
def test_stage_exception_handler_other(error_class):
    # Verify other exceptions are re-raised
    prompt = mock.Mock()
    confirm = mock.Mock()
    err = error_class()
    res = stage_error_handler(err, ['stage'], confirm=confirm, prompt=prompt)
    assert res is None
