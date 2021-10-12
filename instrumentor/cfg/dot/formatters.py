
# return dot language string to add graph edge
def format_edge(from_node, to_node, label=None):
    # return f'"{from_node}" -> "{to_node}"'
    return ' '.join((
        f'"{from_node}" -> "{to_node}"',
        f'[label="{label}"]' if label is not None else '',
    ))


def format_edge_with_label_and_color(from_node, to_node, label, color):
    # return f'"{from_node}" -> "{to_node}"'
    s = None
    if not (label is None and color is None):
        if color is not None and label is not None:
            s = f'[label="{label}" color="{color}"]'
        elif color is None:
            s = f'[label="{label}"]'
        elif label is None:
            s = f'[color="{color}"]'
    return ' '.join((
        f'"{from_node}" -> "{to_node}"',
        s,
    ))