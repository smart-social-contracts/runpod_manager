import os
import time
import json
import traceback
import runpod
from pathlib import Path
from typing import Dict, Optional, List, Any, Tuple

from .config import PodConfig


class PodManager:
    def __init__(
        self,
        project_name: str,
        verbose: bool = False,
        config: Optional[PodConfig] = None,
        **config_kwargs
    ):
        self.verbose = verbose
        
        if config is None:
            self.config = PodConfig(project_name, **config_kwargs)
        else:
            self.config = config
        
        # Initialize RunPod SDK
        runpod.api_key = self.config.api_key
        
    def _print(self, message: str, force: bool = False):
        """Print message if verbose mode is enabled or force is True"""
        if self.verbose or force:
            print(message)
    
    def _find_pod_by_type(self, pod_type: str) -> Tuple[Optional[str], Optional[str]]:
        """Find existing pod by type, returns (pod_id, pod_url) or (None, None) if not found"""
        try:
            # Get all pods
            pods = runpod.get_pods()
            if self.verbose:
                self._print(f"🔍 Found {len(pods)} total pods")
            
            # Look for pods with the naming pattern {project_name}-{pod_type}-*
            pod_name_prefix = self.config.get_pod_name_prefix(pod_type)
            
            for pod in pods:
                pod_name = pod.get('name', '')
                if pod_name.startswith(pod_name_prefix):
                    pod_id = pod.get('id')
                    if pod_id:
                        pod_url = f"{pod_id}-5000.proxy.runpod.net"
                        if self.verbose:
                            self._print(f"✅ Found {pod_type} pod: {pod_name} (ID: {pod_id})")
                        return pod_id, pod_url
            
            if self.verbose:
                self._print(f"❌ No {pod_type} pod found with prefix '{pod_name_prefix}'")
            return None, None
            
        except Exception as e:
            self._print(f"❌ Error finding pod: {e}", force=True)
            return None, None
    
    def _get_pod_url(self, pod_type: str) -> Optional[str]:
        """Get server host based on pod type - now uses dynamic pod discovery"""
        pod_id, pod_url = self._find_pod_by_type(pod_type)
        return pod_url
    
    def _extract_pod_id(self, pod_url: str) -> str:
        """Extract pod ID from server host"""
        return pod_url.split('-')[0]
    
    def get_pod_status(self, pod_id: str) -> str:
        """Get the current status of a pod using RunPod SDK"""
        try:
            pods = runpod.get_pods()
            if self.verbose:
                self._print(f"🔍 Found {len(pods)} total pods")
            
            # Find the specific pod
            for pod in pods:
                if pod['id'] == pod_id:
                    status = pod.get('desiredStatus', 'UNKNOWN')
                    if self.verbose:
                        self._print(f"Pod {pod_id} status: {status}")
                    return status
            
            self._print(f"❌ Pod {pod_id} not found", force=True)
            return 'NOT_FOUND'
                
        except Exception as e:
            self._print(f"❌ Failed to get pod status: {e}", force=True)
            return 'Error'
    
    def wait_for_status(self, pod_id: str, target_statuses: List[str], timeout: int = 300) -> bool:
        """Wait for pod to reach one of the target statuses"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_status = self.get_pod_status(pod_id)
            if current_status in target_statuses:
                return True
            if current_status in ['Error', 'NOT_FOUND']:
                return False
            
            if self.verbose:
                self._print(f"Waiting for pod status... Current: {current_status}")
            time.sleep(5)
        
        return False
    
    def start_pod(self, pod_type: str, deploy_new_if_needed: bool = False) -> bool:
        """Start a pod using RunPod SDK"""
        self._print(f"Starting {pod_type} pod...")
        
        # Find existing pod by name pattern
        pod_id, pod_url = self._find_pod_by_type(pod_type)
        
        if not pod_id:
            self._print(f"❌ No {pod_type} pod found")
            if deploy_new_if_needed:
                self._print("Pod not found, attempting to deploy a new pod...")
                return self.deploy_pod(pod_type)
            else:
                return False
        
        self._print(f"Pod ID: {pod_id}")
        self._print(f"Server Host: {pod_url}")
        
        # Check current status
        current_status = self.get_pod_status(pod_id)
        self._print(f"Current status: {current_status}")
        
        if current_status == "RUNNING":
            self._print("✅ Pod is already running. No action needed.")
            if not self.verbose:
                print("RUNNING")
            return True
        
        if current_status in ['NOT_FOUND', 'Error']:
            if deploy_new_if_needed:
                self._print("Pod not found, attempting to deploy a new pod...")
                return self.deploy_pod(pod_type)
            else:
                self._print("❌ Pod not found and deploy_new_if_needed is False", force=True)
                return False
        
        # Start the pod using RunPod SDK
        self._print(f"Starting pod {pod_id}...")
        try:
            result = runpod.resume_pod(pod_id=pod_id, gpu_count=int(self.config.get('GPU_COUNT', 1)))
            if self.verbose:
                self._print(f"🔍 Start result: {result}")
            
            self._print("Start command sent. Waiting for pod to start...")
            
            if self.wait_for_status(pod_id, ["RUNNING"]):
                self._print("✅ Pod is now running successfully!")
                if not self.verbose:
                    print("RUNNING")
                return True
            else:
                self._print("❌ Pod failed to start", force=True)
                if deploy_new_if_needed:
                    self._print("Pod failed to start, attempting to deploy a new pod...")
                    return self.deploy_pod(pod_type)
                return False
                
        except Exception as e:
            self._print(f"❌ Start failed: {e}", force=True)
            if deploy_new_if_needed:
                self._print("Start command failed, terminating current pod and attempting to deploy a new pod...")
                self.terminate_pod(pod_type)
                return self.deploy_pod(pod_type)
            return False
    
    def stop_pod(self, pod_type: str) -> bool:
        """Stop a pod using RunPod SDK"""
        self._print(f"Stopping {pod_type} pod...")
        
        # Find existing pod by name pattern
        pod_id, pod_url = self._find_pod_by_type(pod_type)
        
        if not pod_id:
            self._print(f"❌ No {pod_type} pod found. No action needed.")
            return True
        
        self._print(f"Pod ID: {pod_id}")
        self._print(f"Server Host: {pod_url}")
        
        # Check current status
        current_status = self.get_pod_status(pod_id)
        self._print(f"Current status: {current_status}")
        
        if current_status in ["EXITED", "STOPPED"]:
            self._print("✅ Pod is already stopped. No action needed.")
            if not self.verbose:
                print(current_status)
            return True
        
        if current_status in ['NOT_FOUND', 'Error']:
            self._print("❌ Pod not found or error getting status", force=True)
            return False
        
        # Stop the pod using RunPod SDK
        self._print(f"Stopping pod {pod_id}...")
        try:
            result = runpod.stop_pod(pod_id)
            if self.verbose:
                self._print(f"🔍 Stop result: {result}")
            
            self._print("Stop command sent. Waiting for pod to stop...")
            
            if self.wait_for_status(pod_id, ["EXITED", "STOPPED"]):
                final_status = self.get_pod_status(pod_id)
                self._print("✅ Pod is now stopped successfully!")
                if not self.verbose:
                    print(final_status)
                return True
            else:
                self._print("❌ Pod failed to stop", force=True)
                return False
                
        except Exception as e:
            self._print(f"❌ Stop failed: {e}", force=True)
            return False
    
    def restart_pod(self, pod_type: str, deploy_new_if_needed: bool = False) -> bool:
        """Restart a pod (stop then start)"""
        self._print(f"Restarting {pod_type} pod...")
        
        # Stop the pod first
        if not self.stop_pod(pod_type):
            self._print("❌ Failed to stop pod for restart", force=True)
            return False
        
        # Start the pod
        return self.start_pod(pod_type, deploy_new_if_needed)
    
    def status_pod(self, pod_type: str) -> bool:
        """Get pod status"""
        # Find existing pod by name pattern
        pod_id, pod_url = self._find_pod_by_type(pod_type)

        pod_url = 'https://' + pod_url if pod_url and not pod_url.startswith('http') else pod_url
        
        if not pod_id:
            self._print(f"❌ No {pod_type} pod found")
            return False
        
        print(f"POD_TYPE={pod_type}")
        print(f"POD_ID={pod_id}")
        print(f"POD_URL={pod_url}")
        
        status = self.get_pod_status(pod_id)
        print(f"POD_STATUS={status}")
        
        return True
    
    def deploy_pod(self, pod_type: str) -> bool:
        """Deploy a new pod using RunPod SDK with the cheapest available GPU"""
        self._print(f"Deploying new {pod_type} pod...")
        
        try:
            # Get available GPU types and their detailed prices
            gpu_types = runpod.get_gpus()
            if self.verbose:
                self._print(f"🔍 Found {len(gpu_types)} GPU types")
            
            # Get detailed pricing for each GPU
            detailed_gpus = []
            print("\n=== Available GPUs with Spot Prices ===")
            print("=" * 60)
            
            for i, gpu_basic in enumerate(gpu_types, 1):
                try:
                    # Get detailed info including pricing for each GPU
                    gpu_detailed = runpod.get_gpu(gpu_basic['id'])
                    detailed_gpus.append(gpu_detailed)
                    
                    name = gpu_detailed.get('displayName', gpu_basic.get('id', 'Unknown'))
                    community_spot = gpu_detailed.get('communitySpotPrice')
                    secure_spot = gpu_detailed.get('secureSpotPrice')
                    
                    print(f'{i:2d}. {name}')
                    print(f'    ID: {gpu_basic.get("id", "N/A")}')
                    
                    if community_spot is not None:
                        print(f'    Community Spot: ${community_spot:.3f}/hr')
                    else:
                        print(f'    Community Spot: N/A')
                        
                    if secure_spot is not None:
                        print(f'    Secure Spot: ${secure_spot:.3f}/hr')
                    else:
                        print(f'    Secure Spot: N/A')
                    
                    # Show lowest price info if available
                    if gpu_detailed.get('lowestPrice'):
                        lowest = gpu_detailed['lowestPrice']
                        if lowest.get('minimumBidPrice'):
                            print(f'    Min Bid: ${lowest["minimumBidPrice"]:.3f}/hr')
                    
                    print()
                    
                except Exception as e:
                    if self.verbose:
                        self._print(f"Warning: Could not get detailed pricing for {gpu_basic.get('id', 'Unknown')}: {e}")
                    # Fallback to basic info
                    detailed_gpus.append(gpu_basic)
            
            print("=" * 60)
            
            # Filter GPUs by price threshold using detailed pricing
            max_price = float(self.config.get('MAX_GPU_PRICE', '0.30'))
            affordable_gpus = []
            
            print(f"\n🔍 Filtering GPUs under ${max_price}/hr...")
            
            for gpu in detailed_gpus:
                community_spot = gpu.get('communitySpotPrice')
                secure_spot = gpu.get('secureSpotPrice')
                
                # Get the minimum available spot price (prefer community over secure)
                min_price = None
                if community_spot is not None:
                    min_price = community_spot
                elif secure_spot is not None:
                    min_price = secure_spot
                
                if min_price is not None and min_price <= max_price:
                    affordable_gpus.append({
                        'id': gpu['id'],
                        'name': gpu.get('displayName', gpu['id']),
                        'price': min_price,
                        'community_spot': community_spot,
                        'secure_spot': secure_spot
                    })
                    if self.verbose:
                        self._print(f"✅ {gpu.get('displayName', gpu['id'])} - ${min_price:.3f}/hr (affordable)")
            
            if not affordable_gpus:
                self._print(f"❌ No GPUs found under ${max_price}/hr", force=True)
                return False
            
            # Sort by price (cheapest first) and try each GPU until one succeeds
            affordable_gpus.sort(key=lambda x: x['price'])
        
            # Create pod using RunPod SDK - try each GPU until one succeeds
            pod_name = self.config.get_pod_name(pod_type, int(time.time()))
            image_name_base = self.config.get('IMAGE_NAME_BASE')
            if image_name_base:
                # Check if the base image already has a tag
                if ':' in image_name_base:
                    # Image already has a tag, use as-is
                    image_name = image_name_base
                else:
                    # No tag, append pod_type as tag
                    image_name = image_name_base + ':' + pod_type
            else:
                # Fallback to a default image if none specified
                image_name = 'runpod/pytorch:latest'
            container_disk = int(self.config.get('CONTAINER_DISK', '20'))
            
            self._print(f"Creating pod: {pod_name}")
            if image_name:
                self._print(f"Image: {image_name}")
            self._print(f"Container Disk: {container_disk}GB")
            
            # Try each affordable GPU until one succeeds
            for i, selected_gpu in enumerate(affordable_gpus):
                try:
                    self._print(f"\n🔄 Trying GPU {i+1}/{len(affordable_gpus)}: {selected_gpu['name']} - ${selected_gpu['price']:.3f}/hr")

                    pod_params = {
                        'name': pod_name,
                        'gpu_type_id': selected_gpu['id'],
                        'gpu_count': int(self.config.get('GPU_COUNT', 1)),
                        'container_disk_in_gb': container_disk,
                        'support_public_ip': self.config.get('SUPPORT_PUBLIC_IP', 'true').lower() == 'true',
                        'start_ssh': self.config.get('START_SSH', 'true').lower() == 'true',
                        'env': {
                            'RUNPOD_API_KEY': self.config.api_key,
                            'POD_TYPE': pod_type,
                            'INACTIVITY_TIMEOUT_SECONDS': self.config.get('INACTIVITY_TIMEOUT_SECONDS', 3600)
                        }
                    }
                    
                    if self.config.get('TEMPLATE_ID'):
                        pod_params['template_id'] = self.config.get('TEMPLATE_ID')
                    
                    # Always include image_name - it's required
                    pod_params['image_name'] = image_name
                    
                    if self.config.get('NETWORK_VOLUME_ID'):
                        pod_params['network_volume_id'] = self.config.get('NETWORK_VOLUME_ID')
                        pod_params['volume_mount_path'] = self.config.get('VOLUME_MOUNT_PATH', '/workspace')

                    # Use the RunPod SDK to create the pod with proper parameters
                    result = runpod.create_pod(**pod_params)
                    
                    if self.verbose:
                        self._print(f"🔍 Create result: {result}")
                    
                    # Extract pod ID from result
                    pod_id = result.get('id') if isinstance(result, dict) else str(result)
                    
                    if pod_id:
                        self._print(f"✅ Pod created successfully with {selected_gpu['name']}!")
                        self._print(f"Pod ID: {pod_id}")
                        
                        # Generate pod URL
                        pod_url = f"https://{pod_id}-5000.proxy.runpod.net"
                        self._print(f"Pod URL: {pod_url}")
                        
                        if not self.verbose:
                            print(pod_id)
                        
                        return True
                    else:
                        self._print(f"⚠️ Pod creation returned no ID for {selected_gpu['name']}, trying next GPU...")
                        continue
                        
                except Exception as gpu_error:
                    error_msg = str(gpu_error)
                    print('Error: ' + error_msg)
                    if "no longer any instances available" in error_msg.lower():
                        self._print(f"⚠️ {selected_gpu['name']} not available, trying next GPU...")
                    elif "insufficient funds" in error_msg.lower():
                        self._print(f"⚠️ Insufficient funds for {selected_gpu['name']}, trying next GPU...")
                    else:
                        self._print(f"⚠️ Error with {selected_gpu['name']}: {error_msg}")
                    
                    # Continue to next GPU
                    continue
            
            # If we get here, all GPUs failed
            self._print(f"❌ All {len(affordable_gpus)} affordable GPUs failed. No pod could be created.", force=True)
            return False
                
        except Exception as e:
            self._print(f"❌ Deployment failed: {e}", force=True)
            traceback.print_exc()
            return False
    
    def terminate_pod(self, pod_type: str) -> bool:
        """Terminate (delete) a pod using RunPod SDK"""
        self._print(f"Terminating {pod_type} pod...")
        
        try:
            # Find existing pod by name pattern
            pod_id, pod_url = self._find_pod_by_type(pod_type)
            
            if not pod_id:
                self._print(f"❌ No {pod_type} pod found")
                return False
            
            self._print(f"Pod ID: {pod_id}")
            self._print(f"Server Host: {pod_url}")
            
            # Delete the pod using RunPod SDK
            result = runpod.terminate_pod(pod_id)
            if self.verbose:
                self._print(f"🔍 Terminate result: {result}")
            
            self._print(f"✅ Pod {pod_id} terminated successfully!")
            if not self.verbose:
                print("TERMINATED")
            return True
                
        except Exception as e:
            self._print(f"❌ Termination failed: {e}", force=True)
            return False
