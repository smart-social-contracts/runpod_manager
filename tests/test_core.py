import pytest
from unittest.mock import patch, MagicMock, call
import time

from runpod_manager.core import PodManager
from runpod_manager.config import PodConfig


class TestPodManager:
    """Test PodManager core functionality"""

    @patch('runpod_manager.core.runpod')
    @patch.dict('os.environ', {'RUNPOD_API_KEY': 'test-key'})
    def test_pod_manager_init(self, mock_runpod):
        """Test PodManager initialization"""
        config = PodConfig("testproject")
        manager = PodManager("testproject", config=config)
        
        assert manager.config == config
        assert manager.verbose is False
        assert mock_runpod.api_key == 'test-key'

    @patch('runpod_manager.core.runpod')
    @patch.dict('os.environ', {'RUNPOD_API_KEY': 'test-key'})
    def test_pod_manager_verbose_mode(self, mock_runpod):
        """Test PodManager with verbose mode"""
        config = PodConfig("testproject")
        manager = PodManager("testproject", verbose=True, config=config)
        
        assert manager.verbose is True

    @patch('runpod_manager.core.runpod')
    @patch.dict('os.environ', {'RUNPOD_API_KEY': 'test-key'})
    def test_find_pod_by_type(self, mock_runpod):
        """Test finding pods by type"""
        mock_pods = [
            {'id': 'pod1', 'name': 'testproject-main-123456'},
            {'id': 'pod2', 'name': 'testproject-branch-789012'},
            {'id': 'pod3', 'name': 'otherproject-main-345678'}
        ]
        mock_runpod.get_pods.return_value = mock_pods
        
        config = PodConfig("testproject")
        manager = PodManager("testproject", config=config)
        
        pod_id, pod_url = manager._find_pod_by_type("main")
        assert pod_id == 'pod1'
        assert pod_url == 'pod1-5000.proxy.runpod.net'
        
        pod_id, pod_url = manager._find_pod_by_type("branch")
        assert pod_id == 'pod2'
        assert pod_url == 'pod2-5000.proxy.runpod.net'
        
        pod_id, pod_url = manager._find_pod_by_type("nonexistent")
        assert pod_id is None
        assert pod_url is None

    @patch('runpod_manager.core.runpod')
    @patch.dict('os.environ', {'RUNPOD_API_KEY': 'test-key'})
    def test_status_pod_exists(self, mock_runpod):
        """Test status_pod when pod exists"""
        mock_pod = {
            'id': 'pod123',
            'name': 'testproject-main-123456',
            'desiredStatus': 'RUNNING',
            'runtime': {'uptimeInSeconds': 3600}
        }
        mock_runpod.get_pods.return_value = [mock_pod]
        
        config = PodConfig("testproject")
        manager = PodManager("testproject", config=config)
        
        result = manager.status_pod("main")
        assert result is True
        mock_runpod.get_pods.assert_called()

    @patch('runpod_manager.core.runpod')
    @patch.dict('os.environ', {'RUNPOD_API_KEY': 'test-key'})
    def test_status_pod_not_found(self, mock_runpod):
        """Test status_pod when pod doesn't exist"""
        mock_runpod.get_pods.return_value = []
        
        config = PodConfig("testproject")
        manager = PodManager("testproject", config=config)
        
        result = manager.status_pod("main")
        assert result is False

    @patch('runpod_manager.core.runpod')
    @patch.dict('os.environ', {'RUNPOD_API_KEY': 'test-key'})
    def test_start_pod_success(self, mock_runpod):
        """Test successful pod start"""
        mock_pod_stopped = {
            'id': 'pod123',
            'name': 'testproject-main-123456',
            'desiredStatus': 'STOPPED'
        }
        mock_pod_running = {
            'id': 'pod123',
            'name': 'testproject-main-123456',
            'desiredStatus': 'RUNNING'
        }
        
        mock_runpod.get_pods.side_effect = [
            [mock_pod_stopped],  # Initial find_pod_by_type call
            [mock_pod_stopped],  # get_pod_status call before start
            [mock_pod_running]   # get_pod_status call after start
        ]
        mock_runpod.resume_pod.return_value = {'status': 'success'}
        
        config = PodConfig("testproject")
        manager = PodManager("testproject", config=config)
        
        result = manager.start_pod("main")
        assert result is True
        mock_runpod.resume_pod.assert_called_once_with(pod_id='pod123', gpu_count=1)

    @patch('runpod_manager.core.runpod')
    @patch.dict('os.environ', {'RUNPOD_API_KEY': 'test-key'})
    def test_stop_pod_success(self, mock_runpod):
        """Test successful pod stop"""
        mock_pod_running = {
            'id': 'pod123',
            'name': 'testproject-main-123456',
            'desiredStatus': 'RUNNING'
        }
        mock_pod_stopped = {
            'id': 'pod123',
            'name': 'testproject-main-123456',
            'desiredStatus': 'STOPPED'
        }
        
        mock_runpod.get_pods.side_effect = [
            [mock_pod_running],  # Initial find_pod_by_type call
            [mock_pod_running],  # get_pod_status call before stop
            [mock_pod_stopped]   # get_pod_status call after stop
        ]
        mock_runpod.stop_pod.return_value = {'status': 'success'}
        
        config = PodConfig("testproject")
        manager = PodManager("testproject", config=config)
        
        result = manager.stop_pod("main")
        assert result is True
        mock_runpod.stop_pod.assert_called_once_with('pod123')

    @patch('runpod_manager.core.runpod')
    @patch.dict('os.environ', {'RUNPOD_API_KEY': 'test-key'})
    def test_terminate_pod_success(self, mock_runpod):
        """Test successful pod termination"""
        mock_pod = {
            'id': 'pod123',
            'name': 'testproject-main-123456'
        }
        mock_runpod.get_pods.return_value = [mock_pod]
        mock_runpod.terminate_pod.return_value = {'status': 'success'}
        
        config = PodConfig("testproject")
        manager = PodManager("testproject", config=config)
        
        result = manager.terminate_pod("main")
        assert result is True
        mock_runpod.terminate_pod.assert_called_once_with('pod123')

    @patch('runpod_manager.core.runpod')
    @patch('runpod_manager.core.time.time')
    @patch.dict('os.environ', {'RUNPOD_API_KEY': 'test-key'})
    def test_deploy_pod_success(self, mock_time, mock_runpod):
        """Test successful pod deployment"""
        mock_time.return_value = 1234567890
        
        mock_gpu_basic = [
            {'id': 'gpu1'},
            {'id': 'gpu2'}
        ]
        mock_gpu_detailed = [
            {'id': 'gpu1', 'displayName': 'RTX 3080', 'communitySpotPrice': 0.25, 'secureSpotPrice': 0.30},
            {'id': 'gpu2', 'displayName': 'RTX 4090', 'communitySpotPrice': 0.45, 'secureSpotPrice': 0.50}
        ]
        
        mock_runpod.get_gpus.return_value = mock_gpu_basic
        mock_runpod.get_gpu.side_effect = mock_gpu_detailed
        mock_runpod.create_pod.return_value = {'id': 'new_pod_123'}
        
        config = PodConfig("testproject")
        config.set('TEMPLATE_ID', 'template123')
        config.set('IMAGE_NAME_BASE', 'docker.io/test/image')
        manager = PodManager("testproject", config=config)
        
        result = manager.deploy_pod("main")
        assert result is True
        
        mock_runpod.create_pod.assert_called_once()
        call_args = mock_runpod.create_pod.call_args[1]
        assert call_args['name'] == 'testproject-main-1234567890'
        assert call_args['image_name'] == 'docker.io/test/image:main'
        assert call_args['gpu_type_id'] == 'gpu1'

    @patch('runpod_manager.core.runpod')
    @patch.dict('os.environ', {'RUNPOD_API_KEY': 'test-key'})
    def test_restart_pod_success(self, mock_runpod):
        """Test successful pod restart"""
        mock_pod_running = {
            'id': 'pod123',
            'name': 'testproject-main-123456',
            'desiredStatus': 'RUNNING'
        }
        mock_pod_stopped = {
            'id': 'pod123',
            'name': 'testproject-main-123456',
            'desiredStatus': 'STOPPED'
        }
        
        mock_runpod.get_pods.side_effect = [
            [mock_pod_running],
            [mock_pod_running],
            [mock_pod_stopped],
            [mock_pod_stopped],
            [mock_pod_stopped],
            [mock_pod_stopped],
            [mock_pod_running]
        ]
        mock_runpod.stop_pod.return_value = {'status': 'success'}
        mock_runpod.resume_pod.return_value = {'status': 'success'}
        
        config = PodConfig("testproject")
        manager = PodManager("testproject", config=config)
        
        result = manager.restart_pod("main")
        assert result is True
        mock_runpod.stop_pod.assert_called_once_with('pod123')
        mock_runpod.resume_pod.assert_called_once_with(pod_id='pod123', gpu_count=1)

    @patch('runpod_manager.core.runpod')
    @patch.dict('os.environ', {'RUNPOD_API_KEY': 'test-key'})
    def test_error_handling(self, mock_runpod):
        """Test error handling in pod operations"""
        mock_runpod.get_pods.side_effect = Exception("API Error")
        
        config = PodConfig("testproject")
        manager = PodManager("testproject", config=config)
        
        result = manager.status_pod("main")
        assert result is False

    @patch('runpod_manager.core.runpod')
    @patch.dict('os.environ', {'RUNPOD_API_KEY': 'test-key'})
    def test_project_name_isolation(self, mock_runpod):
        """Test that different project names are properly isolated"""
        mock_pods = [
            {'id': 'pod1', 'name': 'project1-main-123456'},
            {'id': 'pod2', 'name': 'project2-main-789012'},
            {'id': 'pod3', 'name': 'project1-branch-345678'}
        ]
        mock_runpod.get_pods.return_value = mock_pods
        
        config1 = PodConfig("project1")
        manager1 = PodManager("project1", config=config1)
        pod_id1, pod_url1 = manager1._find_pod_by_type("main")
        assert pod_id1 == 'pod1'
        
        config2 = PodConfig("project2")
        manager2 = PodManager("project2", config=config2)
        pod_id2, pod_url2 = manager2._find_pod_by_type("main")
        assert pod_id2 == 'pod2'
        
        pod_id_branch, pod_url_branch = manager2._find_pod_by_type("branch")
        assert pod_id_branch is None
        assert pod_url_branch is None
