import os
import tempfile
import pytest
from unittest.mock import patch

from runpod_manager.config import PodConfig


class TestPodConfig:
    """Test PodConfig class functionality"""

    def test_config_requires_project_name(self):
        """Test that PodConfig requires a project name"""
        with patch.dict(os.environ, {'RUNPOD_API_KEY': 'test-key'}):
            config = PodConfig("test-project")
            assert config.project_name == "test-project"

    def test_config_requires_api_key(self):
        """Test that PodConfig requires RUNPOD_API_KEY"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="RUNPOD_API_KEY not found"):
                PodConfig("test-project")

    def test_config_from_env_var(self):
        """Test loading API key from environment variable"""
        with patch.dict(os.environ, {'RUNPOD_API_KEY': 'env-test-key'}):
            config = PodConfig("test-project")
            assert config.api_key == "env-test-key"

    def test_config_from_constructor(self):
        """Test providing API key via constructor"""
        config = PodConfig("test-project", api_key="constructor-key")
        assert config.api_key == "constructor-key"

    def test_config_defaults(self):
        """Test default configuration values"""
        with patch.dict(os.environ, {'RUNPOD_API_KEY': 'test-key'}):
            config = PodConfig("test-project")
            assert config.get('MAX_GPU_PRICE') == '0.30'
            assert config.get('CONTAINER_DISK') == '20'
            assert config.get('GPU_COUNT') == '1'
            assert config.get('SUPPORT_PUBLIC_IP') == 'true'

    def test_config_from_file(self):
        """Test loading configuration from file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write("MAX_GPU_PRICE=0.50\n")
            f.write("CONTAINER_DISK=30\n")
            f.write("# This is a comment\n")
            f.write("CUSTOM_VALUE=test\n")
            config_file = f.name

        try:
            with patch.dict(os.environ, {'RUNPOD_API_KEY': 'test-key'}):
                config = PodConfig("test-project", config_file=config_file)
                assert config.get('MAX_GPU_PRICE') == '0.50'
                assert config.get('CONTAINER_DISK') == '30'
                assert config.get('CUSTOM_VALUE') == 'test'
        finally:
            os.unlink(config_file)

    def test_config_kwargs_override(self):
        """Test that kwargs override defaults and file config"""
        with patch.dict(os.environ, {'RUNPOD_API_KEY': 'test-key'}):
            config = PodConfig("test-project", MAX_GPU_PRICE='1.00', CUSTOM_PARAM='value')
            assert config.get('MAX_GPU_PRICE') == '1.00'
            assert config.get('CUSTOM_PARAM') == 'value'

    def test_pod_name_generation(self):
        """Test pod name generation methods"""
        with patch.dict(os.environ, {'RUNPOD_API_KEY': 'test-key'}):
            config = PodConfig("myproject")
            
            assert config.get_pod_name_prefix("main") == "myproject-main-"
            assert config.get_pod_name_prefix("branch") == "myproject-branch-"
            
            timestamp = 1234567890
            assert config.get_pod_name("main", timestamp) == "myproject-main-1234567890"
            assert config.get_pod_name("dev", timestamp) == "myproject-dev-1234567890"

    def test_config_set_get(self):
        """Test setting and getting configuration values"""
        with patch.dict(os.environ, {'RUNPOD_API_KEY': 'test-key'}):
            config = PodConfig("test-project")
            
            config.set('NEW_VALUE', 'test')
            assert config.get('NEW_VALUE') == 'test'
            
            assert config.get('NONEXISTENT', 'default') == 'default'
            assert config.get('NONEXISTENT') is None
