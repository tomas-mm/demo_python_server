# poor man's dependency injection
singletons = {'users': None,
              'levels': None,
              'server': None}


def init_singletons(settings):
    """
    Create storage singletons 
    if the server is multiprocess (actually creates a local sync manager for users and another for levels)
    if the server is multithreaded dictionaries are directly shared using threading.locks to protect them
    if the users are 'non-stored' the tokens are signed using sha1 (they contain the user_id and the timeout)
    and no memory container is created to hold them.
    """
    # import inside the method to avoid circular dependencies (otherwise we
    # would need a new module with only the dictionary)
    from storage import Levels, UsersStored
    from server import server_factory
    from users import UsersNonStored

    forked = not settings.threaded
    singletons['users'] = UsersStored(forked) if settings.store_tokens else UsersNonStored()
    singletons['levels'] = Levels(forked)
    singletons['server'] = server_factory(settings)
