
from slither.core.cfg.node import NodeType, Node

ENTRY_NODE_ID = -1
EXIT_NODE_ID = -2

entry_node = Node(NodeType.PLACEHOLDER, ENTRY_NODE_ID)
exit_node = Node(NodeType.PLACEHOLDER, EXIT_NODE_ID)
