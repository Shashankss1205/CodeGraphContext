def get_mro(class_name: str, hierarchy_lookup) -> list:
    """Recursively compute MRO for a class using INHERITS_FROM edges"""
    mro = [class_name]
    visited = set()

    def dfs(cls):
        if cls in visited:
            return
        visited.add(cls)
        parents = hierarchy_lookup(cls)
        for parent in parents:
            mro.append(parent)
            dfs(parent)

    dfs(class_name)
    mro.append("object")
    return mro
def resolve_super_call(current_class, method_name, method_registry, hierarchy_lookup):
    mro = get_mro(current_class, hierarchy_lookup)
    for cls in mro[1:]:  # Skip current class
        if method_name in method_registry.get(cls, {}):
            return method_registry[cls][method_name]
    return None
