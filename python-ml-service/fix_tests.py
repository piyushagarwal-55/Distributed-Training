"""
Quick fix script to update test files with proper NodeMetadata initialization.
"""

import re
from pathlib import Path

def fix_test_file(file_path):
    """Fix NodeMetadata initialization in test files."""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern 1: status="active" -> status=NodeStatus.READY
    content = re.sub(
        r'status="active"',
        r'status=NodeStatus.READY',
        content
    )
    
    # Pattern 2: Add node_address if missing in NodeMetadata creation
    # Find NodeMetadata calls without node_address
    pattern = r'NodeMetadata\(\s*node_id=f?"([^"]+)",\s*status=NodeStatus\.READY'
    
    def add_node_address(match):
        node_id = match.group(1)
        # Extract index from node_id like "node_{i+1}"
        if "{i+1}" in node_id:
            return f'NodeMetadata(\n                node_id=f"{node_id}",\n                node_address=f"192.168.1.{{i+1}}:8000",\n                status=NodeStatus.READY'
        elif "{i}" in node_id:
            return f'NodeMetadata(\n                node_id=f"{node_id}",\n                node_address=f"192.168.1.{{i}}:8000",\n                status=NodeStatus.READY'
        else:
            return f'NodeMetadata(\n                node_id="{node_id}",\n                node_address="192.168.1.1:8000",\n                status=NodeStatus.READY'
    
    content = re.sub(pattern, add_node_address, content)
    
    # Also handle test_node pattern
    content = content.replace(
        'NodeMetadata(node_id="test_node", status=NodeStatus.READY)',
        'NodeMetadata(node_id="test_node", node_address="192.168.1.1:8000", status=NodeStatus.READY)'
    )
    
    # Remove old capabilities field
    content = re.sub(
        r',\s*capabilities=\{[^}]+\}',
        '',
        content
    )
    
    # Make sure NodeStatus is imported
    if 'from src.models.node import' in content:
        if 'NodeStatus' not in content.split('from src.models.node import')[1].split('\n')[0]:
            content = content.replace(
                'from src.models.node import NodeMetadata',
                'from src.models.node import NodeMetadata, NodeStatus'
            )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✓ Fixed {file_path}")

# Fix all test files
test_files = [
    'tests/test_resilience.py',
    'tests/test_performance.py'
]

for file in test_files:
    path = Path(__file__).parent / file
    if path.exists():
        fix_test_file(path)
    else:
        print(f"✗ File not found: {file}")

print("\n✓ All test files updated!")
