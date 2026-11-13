class AIServiceError(Exception):
    """Base exception for AI Service errors."""
    def __init__(self, message: str = "An error occurred with the AI service."):
        self.message = message
        super().__init__(self.message)

class AIConfigurationError(AIServiceError):
    """Raised when xAI API key or model is not configured."""
    def __init__(self, message: str = "Generative AI is not configured. Please set XAI_API_KEY."):
        super().__init__(message)

class AIRateLimitError(AIServiceError):
    """Raised when xAI API rate limits are encountered."""
    def __init__(self, message: str = "AI service rate limit reached. Please try again shortly."):
        super().__init__(message)

class AITimeoutError(AIServiceError):
    """Raised when xAI API request times out."""
    def __init__(self, message: str = "AI service request timed out. Please try again."):
        super().__init__(message)

class AIResponseParseError(AIServiceError):
    """Raised when structured JSON response from AI cannot be parsed."""
    def __init__(self, message: str = "Failed to parse structured response from AI model."):
        super().__init__(message)
