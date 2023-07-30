INSTANCES = {}


def singleton(cls, *args, **kwargs):
    """A singleton decorator, taken from https://peps.python.org/pep-0318/#examples

    Parameters
    ----------
    cls : class
        The class to make a singleton

    Returns
    -------
    cls : class
        The singleton class

    Examples
    --------
    >>> @singleton
    ... class MyClass:
    ...     pass
    >>> a = MyClass()
    >>> b = MyClass()
    >>> a is b
    True

    """
    global INSTANCES

    def getinstance(*args, **kwargs):
        if cls not in INSTANCES:
            INSTANCES[cls] = cls(*args, **kwargs)
            print(
                f"Creating new instance of {cls.__name__}\n\tINSTANCES: {INSTANCES}\n\tARGS: {args}\n\tKWARGS: {kwargs}"
            )
        return INSTANCES[cls]

    return getinstance
