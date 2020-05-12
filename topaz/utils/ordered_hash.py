import copy
from rpython.rlib import jit, objectmodel

class Entry(object):
	_immutable_fields_ = ["hash", "w_key", "w_value"]

	def __init__(self, hash, w_key, w_value):
		self.hash = hash
		self.w_key = w_key
		self.w_value = w_value

	def __deepcopy__(self, memo):
		return Entry(self.hash, self.w_key, self.w_value)


# Super simple implementation of OrderedHash, faster by 8-10 times on get/set operations, than rpython OrderedDict()
class OrderedHash(object):
	def __init__(self, hash_w, eq_w):
		self.hash_w = hash_w
		self.eq_w = eq_w
		self.entries = []
		self.indexes = {}
		self.deleted_count = 0

	def __deepcopy__(self, memo):
		h = OrderedHash(self.hash_w, self.eq_w)
		h.entries = copy.deepcopy(self.entries)
		h.indexes = copy.deepcopy(self.indexes)
		h.deleted_count = self.deleted_count
		return h

	def copy_from(self, other):
		assert isinstance(other, OrderedHash)
		self.clear()
		for entry, _ in other.each():
			# TODO: optimize
			self._put_impl(entry.hash, entry.w_key, entry.w_value)

	def put(self, w_key, w_value):
		hash = self.hash_w(w_key)
		self._put_impl(hash, w_key, w_value)

	def _put_impl(self, hash, w_key, w_value):
		indexes, _, entry = self.find_entry(hash, w_key)

		if entry is None:
			entry = Entry(hash, w_key, w_value)
			self.entries.append(entry)
			entry_id = len(self.entries) - 1

			if indexes is not None:
				indexes.append(entry_id)
			else:
				self.indexes[hash] = [entry_id]
		else:
			entry.w_value = w_value

	def get(self, w_key):
		hash = self.hash_w(w_key)
		_, _, entry = self.find_entry(hash, w_key)
		return entry

	def shift(self):
		for entry, index in self.each():
			# remove entry and return it
			indexes = self.indexes[entry.hash]
			indexes.remove(index)
			self.entries[index] = None
			self.deleted_count += 1
			return entry
		return None

	def remove(self, w_key):
		hash = self.hash_w(w_key)
		return self._remove_impl(hash, w_key)

	def _remove_impl(self, hash, w_key):
		indexes, index, entry = self.find_entry(hash, w_key)
		if entry is not None:
			self.entries[index] = None
			indexes.remove(index)
			self.deleted_count += 1
		return entry

	def clear(self):
		self.entries = []
		self.indexes = {}
		self.deleted_count = 0

	def len(self):
		return len(self.entries) - self.deleted_count

	def _size(self):
		return len(self.entries)

	def rebuild(self, rehash=True):
		# rehash only if deleted nodes more than 200%
		if self.deleted_count / 2 < self.len():
			return

		#self.deleted_count = 0

	def each(self):
		i = 0
		for entry in self.entries:
			if entry is not None:
				yield entry, i
			i += 1

	@jit.unroll_safe
	def find_entry(self, hash, w_key):
		try:
			indexes = self.indexes[hash]
			for index in indexes:
				entry = self.entries[index]
				if self.eq_w(entry.w_key, w_key):
					return (indexes, index, entry)
			return (indexes, 0, None)
		except KeyError:
			return (None, 0, None)
