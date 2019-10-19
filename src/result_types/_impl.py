"""Implementations of Ok, Err, Some, and None."""

import typing as t
from functools import partial, wraps

from ._interface import _Option, _Result
from ._mixin import Immutable


T = t.TypeVar("T")
E = t.TypeVar("E")
U = t.TypeVar("U")
F = t.TypeVar("F")

ExcType = t.TypeVar("ExcType", bound=Exception)

WrappedFunc = t.Callable[..., t.Any]
WrappedFn = t.TypeVar("WrappedFn", bound=WrappedFunc)

Args = t.TypeVar("Args")
Kwargs = t.TypeVar("Kwargs")

# pylint: disable=super-init-not-called


# pylint: disable=abstract-method
class Result(_Result[T, E]):
    """Base implementation for Result types."""

    __slots__ = ()

    @staticmethod
    def of(  # type: ignore
        fn: t.Callable[..., T],
        *args: t.Any,
        catch: t.Type[ExcType] = Exception,
        **kwargs: t.Any,
    ) -> "Result[T, ExcType]":
        """Call `fn` and wrap its result in an `Ok()`.

        If an exception is intercepted, return `Err(exception)`. By
        default, any `Exception` will be intercepted. If you specify
        `exc_type`, only that exception will be intercepted.
        """
        try:
            return Ok(fn(*args, **kwargs))
        except catch as exc:
            return Err(exc)

    @staticmethod
    def err_if(predicate: t.Callable[[T], bool], value: T) -> "Result[T, T]":
        """Return Err(val) if predicate(val) is True, otherwise Ok(val)."""
        if predicate(value):
            return Err(value)
        return Ok(value)

    @staticmethod
    def ok_if(predicate: t.Callable[[T], bool], value: T) -> "Result[T, T]":
        """Return Ok(val) if predicate(val) is True, otherwise Err(val)."""
        if predicate(value):
            return Ok(value)
        return Err(value)


class Option(_Option[T]):
    """Base implementation for Option types."""

    __slots__ = ()

    @staticmethod
    def of(value: t.Optional[T]) -> "Option[T]":
        """Construct an Option[T] from an Optional[T].

        If the value is None, Nothing() is returned. If the value is
        not None, Some(value) is returned.
        """
        if value is None:
            return Nothing()
        return Some(value)

    @staticmethod
    def nothing_if(predicate: t.Callable[[T], bool], value: T) -> "Option[T]":
        """Return Nothing() if predicate(val) is True, else Some(val)."""
        if predicate(value):
            return Nothing()
        return Some(value)

    @staticmethod
    def some_if(predicate: t.Callable[[T], bool], value: T) -> "Option[T]":
        """Return Some(val) if predicate(val) is True, else Nothing()."""
        if predicate(value):
            return Some(value)
        return Nothing()


# pylint: enable=abstract-method


class Ok(Result[T, E], Immutable):
    """Standard wrapper for results."""

    __slots__ = ("_value",)

    def __init__(self, result: T) -> None:
        """Wrap a result."""
        self._value: T = result
        Immutable.__init__(self)

    def and_(self, res: "_Result[U, E]") -> "_Result[U, E]":
        """Return `res` if the result is `Ok`, otherwise return `self`."""
        return res

    def or_(self, res: "_Result[T, F]") -> "_Result[T, F]":
        """Return `res` if the result is `Err`, otherwise `self`."""
        return t.cast(Result[T, F], self)

    def and_then(self, fn: t.Callable[[T], "_Result[U, E]"]) -> "_Result[U, E]":
        """Call `fn` if Ok, or ignore an error.

        This can be used to chain functions that return results.
        """
        return fn(self._value)

    def flatmap(self, fn: t.Callable[[T], "_Result[U, E]"]) -> "_Result[U, E]":
        """Call `fn` if Ok, or ignore an error.

        This can be used to chain functions that return results.
        """
        return self.and_then(fn)

    def or_else(self, fn: t.Callable[[E], "_Result[T, F]"]) -> "_Result[T, F]":
        """Return `self` if `Ok`, or call `fn` with `self` if `Err`."""
        return t.cast(Result[T, F], self)

    def err(self) -> _Option[E]:
        """Return Err value if result is Err."""
        return Nothing()

    def ok(self) -> _Option[T]:
        """Return OK value if result is Ok."""
        return Some(self._value)

    def expect(self, msg: str, exc_cls: t.Type[Exception] = RuntimeError) -> T:
        """Return `Ok` value or raise an error with the specified message.

        The raised exception class may be specified with the `exc_cls`
        keyword argument.
        """
        return self._value

    def expect_err(
        self, msg: str, exc_cls: t.Type[Exception] = RuntimeError
    ) -> E:
        """Return `Err` value or raise an error with the specified message.

        The raised exception class may be specified with the `exc_cls`
        keyword argument.
        """
        raise exc_cls(msg)

    def is_err(self) -> bool:
        """Returl whether the result is an Err."""
        return False

    def is_ok(self) -> bool:
        """Return whether the result is OK."""
        return True

    def iter(self) -> t.Iterator[T]:
        """Return a one-item iterator whose sole member is the result if `Ok`.

        If the result is `Err`, the iterator will contain no items.
        """
        return iter(self)

    def map(self, fn: t.Callable[[T], U]) -> "_Result[U, E]":
        """Map a function onto an okay result, or ignore an error."""
        return Ok(fn(self._value))

    def map_err(self, fn: t.Callable[[E], F]) -> "_Result[T, F]":
        """Map a function onto an error, or ignore a success."""
        return t.cast(Result[T, F], self)

    def unwrap(self) -> T:
        """Return an Ok result, or throw an error if an Err."""
        return self._value

    def unwrap_err(self) -> E:
        """Return an Ok result, or throw an error if an Err."""
        raise RuntimeError(f"Tried to unwrap_err {self}!")

    def unwrap_or(self, alternative: U) -> t.Union[T, U]:
        """Return the `Ok` value, or `alternative` if `self` is `Err`."""
        return self._value

    def unwrap_or_else(self, fn: t.Callable[[E], U]) -> t.Union[T, U]:
        """Return the `Ok` value, or the return from `fn`."""
        return self._value

    def unsafe_unwrap(self) -> t.Union[T, E]:
        """Return the value, regardless of whether we are OK or Err."""
        return self._value

    def __iter__(self) -> t.Iterator[T]:
        """Return a one-item iterator whose sole member is the result if `Ok`.

        If the result is `Err`, the iterator will contain no items.
        """
        yield self._value

    def __eq__(self, other: t.Any) -> bool:
        """Compare two results. They are equal if their values are equal."""
        if not isinstance(other, Result):
            return False
        if not other.is_ok():
            return False
        eq: bool = self._value == other.unwrap()
        return eq

    def __ne__(self, other: t.Any) -> bool:
        """Compare two results. They are equal if their values are equal."""
        return not self == other

    def __str__(self) -> str:
        """Return string value of result."""
        return f"{self.__class__.__name__}({repr(self._value)})"

    def __repr__(self) -> str:
        """Return repr for result."""
        return self.__str__()


class Err(Result[T, E], Immutable):
    """Standard wrapper for results."""

    __slots__ = ("_value",)

    def __init__(self, result: E) -> None:
        """Wrap a result."""
        self._value = result
        Immutable.__init__(self)

    def and_(self, res: "_Result[U, E]") -> "_Result[U, E]":
        """Return `res` if the result is `Ok`, otherwise return `self`."""
        return t.cast(Result[U, E], self)

    def or_(self, res: "_Result[T, F]") -> "_Result[T, F]":
        """Return `res` if the result is `Err`, otherwise `self`."""
        return res

    def and_then(self, fn: t.Callable[[T], "_Result[U, E]"]) -> "_Result[U, E]":
        """Call `fn` if Ok, or ignore an error.

        This can be used to chain functions that return results.
        """
        return t.cast(Result[U, E], self)

    def flatmap(self, fn: t.Callable[[T], "_Result[U, E]"]) -> "_Result[U, E]":
        """Call `fn` if Ok, or ignore an error.

        This can be used to chain functions that return results.
        """
        return self.and_then(fn)

    def or_else(self, fn: t.Callable[[E], "_Result[T, F]"]) -> "_Result[T, F]":
        """Return `self` if `Ok`, or call `fn` with `self` if `Err`."""
        return fn(self._value)

    def err(self) -> _Option[E]:
        """Return Err value if result is Err."""
        return Some(self._value)

    def ok(self) -> _Option[T]:
        """Return OK value if result is Ok."""
        return Nothing()

    def expect(self, msg: str, exc_cls: t.Type[Exception] = RuntimeError) -> T:
        """Return `Ok` value or raise an error with the specified message.

        The raised exception class may be specified with the `exc_cls`
        keyword argument.
        """
        raise exc_cls(msg)

    def expect_err(
        self, msg: str, exc_cls: t.Type[Exception] = RuntimeError
    ) -> E:
        """Return `Err` value or raise an error with the specified message.

        The raised exception class may be specified with the `exc_cls`
        keyword argument.
        """
        return self._value

    def is_err(self) -> bool:
        """Returl whether the result is an Err."""
        return True

    def is_ok(self) -> bool:
        """Return whether the result is OK."""
        return False

    def iter(self) -> t.Iterator[T]:
        """Return a one-item iterator whose sole member is the result if `Ok`.

        If the result is `Err`, the iterator will contain no items.
        """
        return iter(self)

    def map(self, fn: t.Callable[[T], U]) -> "_Result[U, E]":
        """Map a function onto an okay result, or ignore an error."""
        return t.cast(Result[U, E], self)

    def map_err(self, fn: t.Callable[[E], F]) -> "_Result[T, F]":
        """Map a function onto an error, or ignore a success."""
        return Err(fn(self._value))

    def unwrap(self) -> T:
        """Return an Ok result, or throw an error if an Err."""
        raise RuntimeError(f"Tried to unwrap {self}!")

    def unwrap_err(self) -> E:
        """Return an Ok result, or throw an error if an Err."""
        return self._value

    def unwrap_or(self, alternative: U) -> t.Union[T, U]:
        """Return the `Ok` value, or `alternative` if `self` is `Err`."""
        return alternative

    def unwrap_or_else(self, fn: t.Callable[[E], U]) -> t.Union[T, U]:
        """Return the `Ok` value, or the return from `fn`."""
        return fn(self._value)

    def unsafe_unwrap(self) -> t.Union[T, E]:
        """Return the value, regardless of whether we are OK or Err."""
        return self._value

    def __iter__(self) -> t.Iterator[T]:
        """Return a one-item iterator whose sole member is the result if `Ok`.

        If the result is `Err`, the iterator will contain no items.
        """
        _: t.Tuple[T, ...] = ()
        yield from _

    def __eq__(self, other: t.Any) -> bool:
        """Compare two results. They are equal if their values are equal."""
        if not isinstance(other, Result):
            return False
        if not other.is_err():
            return False
        eq: bool = self._value == other.unwrap_err()
        return eq

    def __ne__(self, other: t.Any) -> bool:
        """Compare two results. They are equal if their values are equal."""
        return not self == other

    def __str__(self) -> str:
        """Return string value of result."""
        return f"{self.__class__.__name__}({repr(self._value)})"

    def __repr__(self) -> str:
        """Return repr for result."""
        return self.__str__()


class Some(Option[T], Immutable):
    """A value that may be `Some` or `Nothing`."""

    __slots__ = ("_value",)

    def __init__(self, value: T) -> None:
        """Wrap value in a `Some()`."""
        self._value = value
        Immutable.__init__(self)

    def and_(self, alternative: _Option[U]) -> _Option[U]:
        """Return `Nothing` if `self` is `Nothing`, or the `alternative`."""
        return alternative

    def or_(self, alternative: _Option[T]) -> _Option[T]:
        """Return option if it is `Some`, or the `alternative`."""
        return self

    def xor(self, alternative: _Option[T]) -> _Option[T]:
        """Return Some IFF exactly one of `self`, `alternative` is `Some`."""
        return (
            t.cast(_Option[T], self) if alternative.is_nothing() else Nothing()
        )

    def and_then(self, fn: t.Callable[[T], _Option[U]]) -> _Option[U]:
        """Return `Nothing`, or call `fn` with the `Some` value."""
        return fn(self._value)

    def flatmap(self, fn: t.Callable[[T], "_Option[U]"]) -> "_Option[U]":
        """Return `Nothing`, or call `fn` with the `Some` value."""
        return self.and_then(fn)

    def or_else(self, fn: t.Callable[[], _Option[T]]) -> _Option[T]:
        """Return option if it is `Some`, or calculate an alternative."""
        return self

    def expect(self, msg: str, exc_cls: t.Type[Exception] = RuntimeError) -> T:
        """Unwrap and yield a `Some`, or throw an exception if `Nothing`.

        The exception class may be specified with the `exc_cls` keyword
        argument.
        """
        return self._value

    def filter(self, predicate: t.Callable[[T], bool]) -> _Option[T]:
        """Return `Nothing`, or an option determined by the predicate.

        If `self` is `Some`, call `predicate` with the wrapped value and
        return:

        * `self` (`Some(t)` where `t` is the wrapped value) if the predicate
          is `True`
        * `Nothing` if the predicate is `False`
        """
        if predicate(self._value):
            return self
        return Nothing()

    def is_nothing(self) -> bool:
        """Return whether the option is `Nothing`."""
        return False

    def is_some(self) -> bool:
        """Return whether the option is a `Some` value."""
        return True

    def iter(self) -> t.Iterator[T]:
        """Return an iterator over the possibly contained value."""
        return iter(self)

    def map(self, fn: t.Callable[[T], U]) -> _Option[U]:
        """Apply `fn` to the contained value if any."""
        return Some(fn(self._value))

    def map_or(self, default: U, fn: t.Callable[[T], U]) -> U:
        """Apply `fn` to contained value, or return the default."""
        return fn(self._value)

    def map_or_else(
        self, default: t.Callable[[], U], fn: t.Callable[[T], U]
    ) -> U:
        """Apply `fn` to contained value, or compute a default."""
        return fn(self._value)

    def ok_or(self, err: E) -> Result[T, E]:
        """Transform an option into a `Result`.

        Maps `Some(v)` to `Ok(v)` or `None` to `Err(err)`.
        """
        res: Result[T, E] = Ok(t.cast(T, self._value))
        return res

    def ok_or_else(self, err_fn: t.Callable[[], E]) -> Result[T, E]:
        """Transform an option into a `Result`.

        Maps `Some(v)` to `Ok(v)` or `None` to `Err(err_fn())`.
        """
        res: Result[T, E] = Ok(t.cast(T, self._value))
        return res

    def unwrap(self) -> T:
        """Return `Some` value, or raise an error."""
        return self._value

    def unwrap_or(self, default: U) -> t.Union[T, U]:
        """Return the contained value or `default`."""
        return self._value

    def unwrap_or_else(self, fn: t.Callable[[], U]) -> t.Union[T, U]:
        """Return the contained value or calculate a default."""
        return self._value

    def __iter__(self) -> t.Iterator[T]:
        """Iterate over the contained value if present."""
        yield self._value

    def __eq__(self, other: t.Any) -> bool:
        """Options are equal if their values are equal."""
        if not isinstance(other, Some):
            return False
        eq: bool = self._value == other.unwrap()
        return eq

    def __ne__(self, other: t.Any) -> bool:
        """Options are equal if their values are equal."""
        return not self == other

    def __str__(self) -> str:
        """Represent the Some() as a string."""
        return f"Some({repr(self._value)})"

    def __repr__(self) -> str:
        """Return a string representation of the Some()."""
        return self.__str__()


class Nothing(Option[T], Immutable):
    """A value that may be `Some` or `Nothing`."""

    __slots__ = ("_value",)

    _instance = None

    def __init__(self, _: None = None) -> None:
        """Create a Nothing()."""
        if self._instance is None:
            # The singleton is being instantiated the first time
            self._value = None
            Immutable.__init__(self)

    def __new__(cls, _: None = None) -> "Nothing[T]":
        """Ensure we are a singleton."""
        if cls._instance is None:
            # Create the instance
            inst = super().__new__(cls)
            # And instantiate it
            cls.__init__(inst)
            # Then assign it to the class' _instance var, so no other
            # instances can be created
            cls._instance = inst
        return t.cast("Nothing[T]", cls._instance)

    def and_(self, alternative: _Option[U]) -> _Option[U]:
        """Return `Nothing` if `self` is `Nothing`, or the `alternative`."""
        return t.cast(_Option[U], self)

    def or_(self, alternative: _Option[T]) -> _Option[T]:
        """Return option if it is `Some`, or the `alternative`."""
        return alternative

    def xor(self, alternative: _Option[T]) -> _Option[T]:
        """Return Some IFF exactly one of `self`, `alternative` is `Some`."""
        return alternative if alternative.is_some() else self

    def and_then(self, fn: t.Callable[[T], _Option[U]]) -> _Option[U]:
        """Return `Nothing`, or call `fn` with the `Some` value."""
        return t.cast(_Option[U], self)

    def flatmap(self, fn: t.Callable[[T], "_Option[U]"]) -> "_Option[U]":
        """Return `Nothing`, or call `fn` with the `Some` value."""
        return self.and_then(fn)

    def or_else(self, fn: t.Callable[[], _Option[T]]) -> _Option[T]:
        """Return option if it is `Some`, or calculate an alternative."""
        return fn()

    def expect(self, msg: str, exc_cls: t.Type[Exception] = RuntimeError) -> T:
        """Unwrap and yield a `Some`, or throw an exception if `Nothing`.

        The exception class may be specified with the `exc_cls` keyword
        argument.
        """
        raise exc_cls(msg)

    def filter(self, predicate: t.Callable[[T], bool]) -> _Option[T]:
        """Return `Nothing`, or an option determined by the predicate.

        If `self` is `Some`, call `predicate` with the wrapped value and
        return:

        * `self` (`Some(t)` where `t` is the wrapped value) if the predicate
          is `True`
        * `Nothing` if the predicate is `False`
        """
        return self

    def is_nothing(self) -> bool:
        """Return whether the option is `Nothing`."""
        return True

    def is_some(self) -> bool:
        """Return whether the option is a `Some` value."""
        return False

    def iter(self) -> t.Iterator[T]:
        """Return an iterator over the possibly contained value."""
        return iter(self)

    def map(self, fn: t.Callable[[T], U]) -> _Option[U]:
        """Apply `fn` to the contained value if any."""
        return t.cast(_Option[U], self)

    def map_or(self, default: U, fn: t.Callable[[T], U]) -> U:
        """Apply `fn` to contained value, or return the default."""
        return default

    def map_or_else(
        self, default: t.Callable[[], U], fn: t.Callable[[T], U]
    ) -> U:
        """Apply `fn` to contained value, or compute a default."""
        return default()

    def ok_or(self, err: E) -> Result[T, E]:
        """Transform an option into a `Result`.

        Maps `Some(v)` to `Ok(v)` or `None` to `Err(err)`.
        """
        res: Result[T, E] = Err(err)
        return res

    def ok_or_else(self, err_fn: t.Callable[[], E]) -> Result[T, E]:
        """Transform an option into a `Result`.

        Maps `Some(v)` to `Ok(v)` or `None` to `Err(err_fn())`.
        """
        res: Result[T, E] = Err(err_fn())
        return res

    def unwrap(self) -> T:
        """Return `Some` value, or raise an error."""
        raise RuntimeError("Tried to unwrap Nothing")

    def unwrap_or(self, default: U) -> t.Union[T, U]:
        """Return the contained value or `default`."""
        return default

    def unwrap_or_else(self, fn: t.Callable[[], U]) -> t.Union[T, U]:
        """Return the contained value or calculate a default."""
        return fn()

    def __iter__(self) -> t.Iterator[T]:
        """Iterate over the contained value if present."""
        _: t.Tuple[T, ...] = ()
        yield from _

    def __eq__(self, other: t.Any) -> bool:
        """Options are equal if their values are equal."""
        if not isinstance(other, Nothing):
            return False
        return True

    def __ne__(self, other: t.Any) -> bool:
        """Options are equal if their values are equal."""
        return not self == other

    def __str__(self) -> str:
        """Return a string representation of Nothing()."""
        return f"Nothing()"

    def __repr__(self) -> str:
        """Return a string representation of Nothing()."""
        return self.__str__()
