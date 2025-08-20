import pytest
from unittest.mock import patch, MagicMock
import sys
from io import StringIO

from runpod_manager.cli import create_parser, main


class TestCLI:
    """Test CLI interface functionality"""

    def test_create_parser_default_pod_types(self):
        """Test parser creation with default pod types"""
        parser = create_parser()
        
        args = parser.parse_args(['testproject', 'main', 'status'])
        assert args.project_name == 'testproject'
        assert args.pod_type == 'main'
        assert args.action == 'status'

    def test_create_parser_custom_pod_types(self):
        """Test parser creation with custom pod types"""
        custom_types = ['dev', 'staging', 'prod']
        parser = create_parser(custom_types)
        
        args = parser.parse_args(['myproject', 'staging', 'deploy'])
        assert args.project_name == 'myproject'
        assert args.pod_type == 'staging'
        assert args.action == 'deploy'

    def test_parser_all_actions(self):
        """Test that parser accepts all valid actions"""
        parser = create_parser()
        actions = ['start', 'stop', 'restart', 'status', 'deploy', 'terminate']
        
        for action in actions:
            args = parser.parse_args(['testproject', 'main', action])
            assert args.action == action

    def test_parser_optional_arguments(self):
        """Test optional arguments parsing"""
        parser = create_parser()
        
        args = parser.parse_args(['testproject', 'main', 'status', '--verbose'])
        assert args.verbose is True
        
        args = parser.parse_args(['testproject', 'main', 'start', '--deploy-new-if-needed'])
        assert args.deploy_new_if_needed is True
        
        args = parser.parse_args(['testproject', 'main', 'status', '--config-file', '/path/to/config'])
        assert args.config_file == '/path/to/config'

    def test_parser_help_output(self):
        """Test that help output includes examples"""
        parser = create_parser(['main', 'branch'])
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit):
                parser.parse_args(['--help'])
        
        help_output = mock_stdout.getvalue()
        assert 'main start' in help_output
        assert 'branch stop' in help_output
        assert 'Examples:' in help_output

    @patch('runpod_manager.cli.PodManager')
    @patch('runpod_manager.cli.PodConfig')
    def test_main_start_action(self, mock_config, mock_manager):
        """Test main function with start action"""
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        mock_manager_instance = MagicMock()
        mock_manager.return_value = mock_manager_instance
        mock_manager_instance.start_pod.return_value = True

        with patch('sys.argv', ['runpod-manager', 'testproject', 'main', 'start']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        mock_config.assert_called_once_with('testproject', config_file=None)
        mock_manager.assert_called_once_with('testproject', verbose=False, config=mock_config_instance)
        mock_manager_instance.start_pod.assert_called_once_with('main', False)

    @patch('runpod_manager.cli.PodManager')
    @patch('runpod_manager.cli.PodConfig')
    def test_main_deploy_action(self, mock_config, mock_manager):
        """Test main function with deploy action"""
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        mock_manager_instance = MagicMock()
        mock_manager.return_value = mock_manager_instance
        mock_manager_instance.deploy_pod.return_value = True

        with patch('sys.argv', ['runpod-manager', 'myproject', 'branch', 'deploy', '--verbose']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        mock_manager.assert_called_once_with('myproject', verbose=True, config=mock_config_instance)
        mock_manager_instance.deploy_pod.assert_called_once_with('branch')

    @patch('runpod_manager.cli.PodConfig')
    def test_main_config_error(self, mock_config):
        """Test main function with configuration error"""
        mock_config.side_effect = ValueError("RUNPOD_API_KEY not found")

        with patch('sys.argv', ['runpod-manager', 'testproject', 'main', 'status']):
            with patch('sys.stdout', new_callable=StringIO):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

    def test_main_no_args_shows_help(self):
        """Test that running with no arguments shows help"""
        with patch('sys.argv', ['runpod-manager']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1
        
        help_output = mock_stdout.getvalue()
        assert 'usage:' in help_output or len(help_output) > 0

    @patch('runpod_manager.cli.PodManager')
    @patch('runpod_manager.cli.PodConfig')
    def test_main_custom_pod_types(self, mock_config, mock_manager):
        """Test main function with custom pod types"""
        custom_types = ['dev', 'staging']
        
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        mock_manager_instance = MagicMock()
        mock_manager.return_value = mock_manager_instance
        mock_manager_instance.status_pod.return_value = True

        with patch('sys.argv', ['runpod-manager', 'testproject', 'staging', 'status']):
            with pytest.raises(SystemExit) as exc_info:
                main(pod_types=custom_types)
            assert exc_info.value.code == 0

        mock_manager_instance.status_pod.assert_called_once_with('staging')
