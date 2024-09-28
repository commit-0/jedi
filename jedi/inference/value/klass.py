"""
Like described in the :mod:`parso.python.tree` module,
there's a need for an ast like module to represent the states of parsed
modules.

But now there are also structures in Python that need a little bit more than
that. An ``Instance`` for example is only a ``Class`` before it is
instantiated. This class represents these cases.

So, why is there also a ``Class`` class here? Well, there are decorators and
they change classes in Python 3.

Representation modules also define "magic methods". Those methods look like
``py__foo__`` and are typically mappable to the Python equivalents ``__call__``
and others. Here's a list:

====================================== ========================================
**Method**                             **Description**
-------------------------------------- ----------------------------------------
py__call__(arguments: Array)           On callable objects, returns types.
py__bool__()                           Returns True/False/None; None means that
                                       there's no certainty.
py__bases__()                          Returns a list of base classes.
py__iter__()                           Returns a generator of a set of types.
py__class__()                          Returns the class of an instance.
py__simple_getitem__(index: int/str)   Returns a a set of types of the index.
                                       Can raise an IndexError/KeyError.
py__getitem__(indexes: ValueSet)       Returns a a set of types of the index.
py__file__()                           Only on modules. Returns None if does
                                       not exist.
py__package__() -> List[str]           Only on modules. For the import system.
py__path__()                           Only on modules. For the import system.
py__get__(call_object)                 Only on instances. Simulates
                                       descriptors.
py__doc__()                            Returns the docstring for a value.
====================================== ========================================

"""
from jedi import debug
from jedi.parser_utils import get_cached_parent_scope, expr_is_dotted, function_is_property
from jedi.inference.cache import inference_state_method_cache, CachedMetaClass, inference_state_method_generator_cache
from jedi.inference import compiled
from jedi.inference.lazy_value import LazyKnownValues, LazyTreeValue
from jedi.inference.filters import ParserTreeFilter
from jedi.inference.names import TreeNameDefinition, ValueName
from jedi.inference.arguments import unpack_arglist, ValuesArguments
from jedi.inference.base_value import ValueSet, iterator_to_value_set, NO_VALUES
from jedi.inference.context import ClassContext
from jedi.inference.value.function import FunctionAndClassBase
from jedi.inference.gradual.generics import LazyGenericManager, TupleGenericManager
from jedi.plugins import plugin_manager

class ClassName(TreeNameDefinition):

    def __init__(self, class_value, tree_name, name_context, apply_decorators):
        super().__init__(name_context, tree_name)
        self._apply_decorators = apply_decorators
        self._class_value = class_value

class ClassFilter(ParserTreeFilter):

    def __init__(self, class_value, node_context=None, until_position=None, origin_scope=None, is_instance=False):
        super().__init__(class_value.as_context(), node_context, until_position=until_position, origin_scope=origin_scope)
        self._class_value = class_value
        self._is_instance = is_instance

class ClassMixin:
    pass

class ClassValue(ClassMixin, FunctionAndClassBase, metaclass=CachedMetaClass):
    api_type = 'class'