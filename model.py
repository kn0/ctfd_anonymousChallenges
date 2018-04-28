from CTFd.models import db, Challenges


class AnonymousChallenge(Challenges):
    """
    Model for the anonymous challenge type
    """
    __mapper_args__ = {'polymorphic_identity': 'anonymous'}
    id = db.Column(None, db.ForeignKey('challenges.id'), primary_key=True)

    def __init__(self, name, value, category, type='anonymous'):
        self.name = name
        self.value = value
        self.category = category
        self.type = type
