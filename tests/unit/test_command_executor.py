import pytest
from app.services.command_executor import CommandExecutor
from app.models.command import CommandType

def test_create_command_valid_type():
    """Testa criação de comando com tipo válido"""
    executor = CommandExecutor()
    try:
        command_id = executor.create_command('client123', 'js', 'alert("test")')
        assert command_id is not None
    except Exception as e:
        pytest.fail(f"Falha ao criar comando: {str(e)}")
    
def test_create_command_invalid_type():
    """Testa criação de comando com tipo inválido"""
    executor = CommandExecutor()
    with pytest.raises(ValueError):
        executor.create_command('client123', 'invalid', 'content')
        
def test_generate_manipulation_command():
    """Testa geração de comando de manipulação"""
    executor = CommandExecutor()
    command = executor.generate_manipulation_command('test-id', 'ADD', '<p>Test</p>')
    assert 'target_id' in command
    assert 'action' in command
    assert 'content' in command
    
def test_generate_manipulation_command_invalid_action():
    """Testa geração de comando de manipulação com ação inválida"""
    executor = CommandExecutor()
    with pytest.raises(ValueError):
        executor.generate_manipulation_command('test-id', 'INVALID', '<p>Test</p>')
