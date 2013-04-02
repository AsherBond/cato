"""
Exception/Logging classes for Cato/Maestro.

"""

#__all__ = [ 'CatoError', 'MissingArgumentError']

class CatoError(StandardError):
    """
    General Cato error.
    """

    def __init__(self, reason, *args):
        StandardError.__init__(self, reason, *args)
        self.reason = reason

    def __repr__(self):
        return 'CatoError: %s' % self.reason

    def __str__(self):
        return 'CatoError: %s' % self.reason
    
class MissingArgumentError(CatoError):
    """Missing argument error"""
    pass

class UnknownPropertyError(CatoError):
    """Unknown property error"""
    pass

class UnsupportedVersionError(CatoError):
    """Unsupported version error"""
    pass

class UnsupportedArgumentError(CatoError):
    """Unsupported argument error"""
    pass

class InstanceNotFoundError(CatoError):
    """Instance not found error"""
    pass

class BadParameterError(CatoError):
    """Bad parameter error"""
    pass

class DatastoreError(CatoError):
    """Datastore error"""
    pass

class DocumentNotFoundError(DatastoreError):
    """Datastore could not find document error"""
    pass

class TaskSubmitError(CatoError):
    """Error submitting task"""
    pass

class ReportError(CatoError):
    """Error in the 'dash' reporting module."""
    pass

class InternalError(CatoError):
    """Internal cato error used instead of assert"""
    pass


class InfoException(StandardError):
    """A specific handler used to identify messages that are 'info' and not 'error'."""
    def __init__(self, reason, *args):
        StandardError.__init__(self, reason, *args)
        self.reason = reason

    def __repr__(self):
        return self.reason

    def __str__(self):
        return self.reason
    


