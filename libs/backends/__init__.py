import importlib.util
import libs.config
import os.path


_backends = None


def get_backends():
    global _backends

    if _backends is not None:
        return _backends

    _backends = []
    backends_root = os.path.abspath(os.path.dirname(__file__))
    for mod_sec in libs.config.get_value('SYSTEM', 'ENABLE_MODULES').split():
        mod_name = libs.config.get_value(mod_sec, 'MOD_NAME')
        spec = importlib.util.spec_from_file_location(
            'libs.backends.' + mod_name,
            os.path.join(backends_root, mod_name + '.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _backends.append(mod)
    return _backends
