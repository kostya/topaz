import copy

from rpython.rlib.rerased import new_static_erasing_pair

from topaz.module import ClassDef, check_frozen
from topaz.modules.enumerable import Enumerable
from topaz.objects.objectobject import W_Object
from topaz.objects.procobject import W_ProcObject
from topaz.utils.ordered_hash import OrderedHash

# class BaseDictStrategy(object):
#     def __init__(self, space):
#         pass


# class TypedDictStrategyMixin(object):
#     _mixin_ = True

#     def getitem(self, storage, w_key):
#         return self.wrap(self.unerase(storage)[w_key])

#     def setitem(self, storage, w_key, w_value):
#         self.unerase(storage)[self.unwrap(w_key)] = w_value

#     def contains(self, storage, w_key):
#         return self.unwrap(w_key) in self.unerase(storage)

#     def copy(self, storage):
#         return self.erase(self.unerase(storage).copy())

#     def clear(self, storage):
#         self.unerase(storage).clear()

#     def len(self, storage):
#         return len(self.unerase(storage))

#     def bool(self, storage):
#         return bool(self.unerase(storage))

#     def pop(self, storage, w_key, default):
#         key = self.unwrap(w_key)
#         r_dict = self.unerase(storage)
#         w_return = r_dict.get(key, default)
#         try:
#             del r_dict[key]
#         except KeyError:
#             pass
#         return w_return

#     def popitem(self, storage):
#         key, value = self.unerase(storage).popitem()
#         return self.wrap(key), value

#     def keys(self, storage):
#         return [self.wrap(k) for k in self.unerase(storage).keys()]

#     def values(self, storage):
#         return self.unerase(storage).values()

#     def iteritems(self, storage):
#         return self.iter_erase(self.unerase(storage).iteritems())

#     def iternext(self, storage):
#         key, value = self.iter_unerase(storage).next()
#         return self.wrap(key), value


# class ObjectDictStrategy(BaseDictStrategy, TypedDictStrategyMixin):
#     erase, unerase = new_static_erasing_pair("ObjectDictStrategy")
#     iter_erase, iter_unerase = new_static_erasing_pair("ObjectDictStrategyIterator")

#     def get_empty_storage(self, space):
#         return self.erase(r_ordereddict(space.eq_w, space.hash_w))

#     def wrap(self, w_key):
#         return w_key

#     def unwrap(self, w_key):
#         return w_key


# class IdentityDictStrategy(BaseDictStrategy, TypedDictStrategyMixin):
#     erase, unerase = new_static_erasing_pair("IdentityDictStrategy")
#     iter_erase, iter_unerase = new_static_erasing_pair("IdentityDictStrategyIterator")

#     def get_empty_storage(self, space):
#         return self.erase(OrderedDict())

#     def wrap(self, w_key):
#         return w_key

#     def unwrap(self, w_key):
#         return w_key

class W_HashObject(W_Object):
    classdef = ClassDef("Hash", W_Object.classdef)
    classdef.include_module(Enumerable)

    def __init__(self, space, klass=None):
        W_Object.__init__(self, space, klass)
        self.w_default = space.w_nil
        self.default_proc = None
        self.dict = OrderedHash(space.hash_w, space.eq_w)

    def __deepcopy__(self, memo):
        obj = super(W_HashObject, self).__deepcopy__(memo)
        obj.dict = copy.deepcopy(self.dict, memo)
        obj.w_default = self.w_default
        obj.default_proc = copy.deepcopy(self.default_proc)
        return obj

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_HashObject(space, self)

    @classdef.method("initialize")
    @check_frozen()
    def method_initialize(self, space, w_default=None, block=None):
        if w_default is not None:
            if block is not None:
                raise space.error(space.w_ArgumentError, "wrong number of arguments")
            self.w_default = w_default
        if block is not None:
            self.default_proc = block
        return self

    @classdef.method("default")
    def method_default(self, space, w_key=None):
        if self.default_proc is not None and w_key is not None:
            return space.invoke_block(self.default_proc, [self, w_key])
        else:
            return self.w_default

    @classdef.method("default=")
    @check_frozen()
    def method_set_default(self, space, w_defl):
        self.default_proc = None
        self.w_default = w_defl

    @classdef.method("default_proc")
    def method_default_proc(self, space):
        if self.default_proc is None:
            return space.w_nil
        return self.default_proc

    @classdef.method("default_proc=")
    def method_set_default_proc(self, space, w_proc):
        w_new_proc = space.convert_type(w_proc, space.w_proc, "to_proc")
        assert isinstance(w_new_proc, W_ProcObject)
        arity = space.int_w(space.send(w_new_proc, "arity"))
        if arity != 2 and space.is_true(space.send(w_new_proc, "lambda?")):
            raise space.error(space.w_TypeError, "default_proc takes two arguments (2 for %s)" % arity)
        self.default_proc = w_new_proc
        self.w_default = space.w_nil
        return w_proc

    # @classdef.method("compare_by_identity")
    # @check_frozen()
    # def method_compare_by_identity(self, space):
    #     strategy = space.fromcache(IdentityDictStrategy)
    #     storage = strategy.get_empty_storage(space)

    #     iter = self.strategy.iteritems(self.dict_storage)
    #     while True:
    #         try:
    #             w_key, w_value = self.strategy.iternext(iter)
    #         except StopIteration:
    #             break
    #         strategy.setitem(storage, w_key, w_value)
    #     self.strategy = strategy
    #     self.dict_storage = storage
    #     return self

    # @classdef.method("compare_by_identity?")
    # def method_compare_by_identityp(self, space):
    #     return space.newbool(self.strategy is space.fromcache(IdentityDictStrategy))

    @classdef.method("rehash")
    @check_frozen()
    def method_rehash(self, space):
        self.dict.rebuild()
        return self

    @classdef.method("[]")
    def method_subscript(self, space, w_key):
        entry = self.dict.get(w_key)
        if entry is not None:
            return entry.w_value
        else:
            return space.send(self, "default", [w_key])

    @classdef.method("fetch")
    def method_fetch(self, space, w_key, w_value=None, block=None):
        entry = self.dict.get(w_key)
        if entry is not None:
            return entry.w_value
        else:
            if block is not None:
                return space.invoke_block(block, [w_key])
            elif w_value is not None:
                return w_value
            else:
                raise space.error(space.w_KeyError, "key not found: %s" % space.send(w_key, "inspect"))

    @classdef.method("store")
    @classdef.method("[]=")
    @check_frozen()
    def method_subscript_assign(self, space, w_key, w_value):
        if (space.is_kind_of(w_key, space.w_string) and
            not space.is_true(space.send(w_key, "frozen?"))):

            w_key = space.send(w_key, "dup")
            w_key = space.send(w_key, "freeze")

        self.dict.put(w_key, w_value)
        return w_value

    @classdef.method("length")
    @classdef.method("size")
    def method_size(self, space):
        return space.newint(self.dict.len())

    @classdef.method("empty?")
    def method_emptyp(self, space):
        return space.newbool(self.dict.len() == 0)

    @classdef.method("delete")
    @check_frozen()
    def method_delete(self, space, w_key, block):
        entry = self.dict.remove(w_key)
        if entry is None:
            if block:
                return space.invoke_block(block, [w_key])
            return space.w_nil
        else:
            return entry.w_value

    @classdef.method("clear")
    @check_frozen()
    def method_clear(self, space):
        self.dict.clear()
        return self

    @classdef.method("shift")
    @check_frozen()
    def method_shift(self, space):
        entry = self.dict.shift()
        if entry is not None:
            return space.newarray([entry.w_key, entry.w_value])
        else:
            return space.send(self, "default", [space.w_nil])

    @classdef.method("initialize_copy")
    @classdef.method("replace")
    @check_frozen()
    def method_replace(self, space, w_hash):
        w_hash = space.convert_type(w_hash, space.w_hash, "to_hash")
        assert isinstance(w_hash, W_HashObject)
        self.dict.copy_from(w_hash.dict)
        self.w_default = w_hash.w_default
        self.default_proc = w_hash.default_proc
        return self

    @classdef.method("keys")
    def method_keys(self, space):
        return space.newarray([entry.w_key for entry, _ in self.dict.each()])

    @classdef.method("values")
    def method_values(self, space):
        return space.newarray([entry.w_value for entry, _ in self.dict.each()])

    @classdef.method("to_hash")
    def method_to_hash(self, space):
        return self

    @classdef.method("key?")
    @classdef.method("has_key?")
    @classdef.method("member?")
    @classdef.method("include?")
    def method_includep(self, space, w_key):
        entry = self.dict.get(w_key)
        return space.newbool(entry is not None)


class W_HashIterator(W_Object):
    classdef = ClassDef("HashIterator", W_Object.classdef)

    def __init__(self, space):
        W_Object.__init__(self, space)

    @classdef.singleton_method("allocate")
    def method_allocate(self, space):
        return W_HashIterator(space)

    @classdef.method("initialize")
    def method_initialize(self, w_obj):
        assert isinstance(w_obj, W_HashObject)
        self.id = 0
        self.count = w_obj.dict._size()
        self.dict = w_obj.dict
        return self

    @classdef.method("next")
    def method_next(self, space):
        while self.id < self.count:
            entry = self.dict.entries[self.id]
            self.id += 1
            if entry is not None:
                return space.newarray([entry.w_key, entry.w_value])
        raise space.error(space.w_StopIteration)
