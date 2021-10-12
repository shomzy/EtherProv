from cfg.utils import full_node_id


class MyEdge:
    _running_edge_id = [0]

    def __init__(self, from_node, to_node):
        self._edge_id = self._running_edge_id[0]
        self._running_edge_id[0] = self._running_edge_id[0] + 1

        self._from_node = from_node
        self._to_node = to_node

        self._back_edge_entry_mapping = None
        self._back_edge_exit_mapping = None
        self._true_son = False
        self._false_son = False
        self._is_call_site = False
        self._related_to_call_site_edge_id = None
        self._init = None
        self._inc = None
        self._re_init = None

    def copy_properties_to(self, target):
        target._back_edge_entry_mapping = self._back_edge_entry_mapping
        target._back_edge_exit_mapping = self._back_edge_exit_mapping
        target._true_son = self._true_son
        target._false_son = self._false_son
        target._is_call_site = self._is_call_site
        target._related_to_call_site_edge_id = self._related_to_call_site_edge_id
        target._init = self._init
        target._inc = self._inc
        target._re_init = self._re_init

    def is_instrumented(self):
        res = self._init is not None or \
               self._inc is not None or \
               self._re_init is not None
        return res

    @property
    def edge_id(self):
        return self._edge_id

    @property
    def from_node(self):
        return self._from_node

    @property
    def to_node(self):
        return self._to_node

    @property
    def back_edge_entry_mapping(self):
        return self._back_edge_entry_mapping

    @back_edge_entry_mapping.setter
    def back_edge_entry_mapping(self, value):
        self._back_edge_entry_mapping = value

    @property
    def back_edge_exit_mapping(self):
        return self._back_edge_exit_mapping

    @back_edge_exit_mapping.setter
    def back_edge_exit_mapping(self, value):
        self._back_edge_exit_mapping = value


    def __str__(self):

        from_node = None
        to_node = None

        if self._from_node.node_id < 0:
            from_node = self._from_node.node_id
        else:
            # from_node = full_node_id(self._from_node.function, self._from_node.node_id)
            from_node = full_node_id(self._from_node)

        if self._to_node.node_id < 0:
            to_node = self._to_node.node_id
        else:
            # to_node = full_node_id(self._to_node.function, self._to_node.node_id)
            to_node = full_node_id(self._to_node)

        return f'{from_node} -> {to_node}'
