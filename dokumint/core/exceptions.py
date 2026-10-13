class InvalidDocumentType(Exception):
    """
    Exception indicating an invalid document type was provided for the current function
    This exception could be raised even if a document type is present ot absent.
    """
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidOrMissingDocument(Exception):
    """
    Exception indcating an invalid or missing document was provided
    """
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class InvalidCloudStorage(Exception):
    """
    Exception indicating that the cloud storage of user is missing or corrupt
    """
    def __init__(self, *args: object) -> None:
        super().__init__(*args)