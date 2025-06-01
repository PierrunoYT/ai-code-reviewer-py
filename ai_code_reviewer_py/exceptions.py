class AIReviewerException(Exception):
    pass

class ReviewParsingError(AIReviewerException):
    pass

class ReviewGenerationError(AIReviewerException):
    pass

class GitSecurityError(AIReviewerException):
    pass