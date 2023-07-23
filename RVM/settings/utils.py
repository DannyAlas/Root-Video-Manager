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
    instances = {}

    def getinstance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return getinstance
