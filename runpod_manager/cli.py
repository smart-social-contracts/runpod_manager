import sys
import argparse
from typing import List, Optional

from .core import PodManager
from .config import PodConfig


def create_parser(pod_types: Optional[List[str]] = None) -> argparse.ArgumentParser:
    """Create argument parser with configurable pod types"""
    if pod_types is None:
        pod_types = ['main', 'branch']
    
    parser = argparse.ArgumentParser(
        description="RunPod Manager - Manage RunPod instances using the official RunPod SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  %(prog)s {pod_types[0]} start     - Start the {pod_types[0]} pod
  %(prog)s {pod_types[-1]} stop    - Stop the {pod_types[-1]} pod
  %(prog)s {pod_types[0]} restart   - Restart the {pod_types[0]} pod
  %(prog)s {pod_types[-1]} status  - Get {pod_types[-1]} pod status
  %(prog)s {pod_types[0]} deploy    - Deploy new {pod_types[0]} pod with cheapest GPU
  %(prog)s {pod_types[-1]} terminate - Terminate (delete) the {pod_types[-1]} pod
  %(prog)s {pod_types[0]} start --deploy-new-if-needed - Start pod, deploy new if needed
  %(prog)s {pod_types[-1]} restart --deploy-new-if-needed - Restart pod, deploy new if needed
        """
    )
    
    parser.add_argument('project_name', 
                       help='Project name for pod naming')
    parser.add_argument('pod_type', choices=pod_types, 
                       help='Pod type to manage')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'deploy', 'terminate'],
                       help='Action to perform')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output (default: concise)')
    parser.add_argument('--deploy-new-if-needed', action='store_true',
                       help='Deploy a new pod if current one cannot be started (for start/restart only)')
    parser.add_argument('--config-file', 
                       help='Path to configuration file')
    
    return parser


def main(pod_types: Optional[List[str]] = None):
    """Main CLI entry point"""
    parser = create_parser(pod_types)
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    try:
        config = PodConfig(args.project_name, config_file=args.config_file)
        manager = PodManager(args.project_name, verbose=args.verbose, config=config)
        
        if args.action == 'start':
            success = manager.start_pod(args.pod_type, args.deploy_new_if_needed)
        elif args.action == 'stop':
            success = manager.stop_pod(args.pod_type)
        elif args.action == 'restart':
            success = manager.restart_pod(args.pod_type, args.deploy_new_if_needed)
        elif args.action == 'status':
            success = manager.status_pod(args.pod_type)
        elif args.action == 'deploy':
            success = manager.deploy_pod(args.pod_type)
        elif args.action == 'terminate':
            success = manager.terminate_pod(args.pod_type)
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
