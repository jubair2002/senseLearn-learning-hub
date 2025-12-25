# Security Module

This module provides comprehensive security features for the SenseLearn application.

## Structure

```
src/security/
├── __init__.py              # Module exports
├── rate_limiter.py          # Rate limiting to prevent abuse
├── csrf.py                  # CSRF protection
├── input_validator.py       # Input validation and sanitization
├── password_validator.py    # Password strength validation
├── security_headers.py      # Security HTTP headers
├── account_lockout.py       # Account lockout after failed attempts
├── security_logger.py       # Security event logging
├── security_init.py         # Security initialization
└── README.md               # This file
```

## Features

### 1. Rate Limiting
Prevents brute force attacks and API abuse by limiting requests per IP/user.

**Usage:**
```python
from src.security import rate_limit

@app.route('/api/login')
@rate_limit(max_requests=5, window_seconds=300)  # 5 requests per 5 minutes
def login():
    ...
```

### 2. CSRF Protection
Protects against Cross-Site Request Forgery attacks.

**Usage:**
```python
from src.security import csrf_protect

@app.route('/api/update')
@csrf_protect
def update():
    ...
```

**Frontend:**
Include CSRF token in requests:
- Header: `X-CSRF-Token: <token>`
- Form data: `csrf_token: <token>`
- Template: `{{ csrf_token }}`

### 3. Input Validation
Validates and sanitizes user input to prevent injection attacks.

**Usage:**
```python
from src.security import InputValidator, sanitize_input, validate_and_sanitize

# Simple validation
if not InputValidator.validate_email(email):
    return error("Invalid email")

# Sanitization
clean_input = sanitize_input(user_input, input_type='text')

# Schema-based validation
schema = {
    'email': {'type': 'email', 'required': True},
    'name': {'type': 'text', 'required': True, 'max_length': 255},
}
data, errors = validate_and_sanitize(request.json, schema)
```

### 4. Password Validation
Ensures users create strong passwords.

**Usage:**
```python
from src.security import PasswordValidator

validator = PasswordValidator(
    min_length=8,
    require_uppercase=True,
    require_lowercase=True,
    require_digit=True,
    require_special=True
)

is_valid, errors = validator.validate(password)
strength = validator.calculate_strength(password)  # 'weak', 'medium', 'strong'
```

### 5. Security Headers
Adds security HTTP headers to all responses.

Automatically initialized when `init_security(app)` is called.

### 6. Account Lockout
Locks accounts after multiple failed login attempts.

**Usage:**
```python
from src.security import get_account_lockout

lockout = get_account_lockout()

# Check if locked
is_locked, until = lockout.is_locked(email)
if is_locked:
    return error("Account locked")

# Record failed attempt
lockout.record_failed_attempt(email)

# Record successful attempt
lockout.record_successful_attempt(email)
```

### 7. Security Logging
Logs security events for monitoring and auditing.

**Usage:**
```python
from src.security import SecurityLogger

SecurityLogger.log_failed_login(email, "Invalid password")
SecurityLogger.log_suspicious_activity("SQL injection attempt", {"input": value})
```

## Integration

Add to your `src/__init__.py`:

```python
from src.security import init_security

def create_app():
    app = Flask(__name__)
    # ... other initialization ...
    
    # Initialize security features
    init_security(app)
    
    return app
```

## Best Practices

1. **Always validate input** before processing
2. **Use rate limiting** on authentication endpoints
3. **Enable CSRF protection** on state-changing operations
4. **Log security events** for monitoring
5. **Use strong password requirements**
6. **Lock accounts** after failed attempts
7. **Sanitize user input** before storing or displaying

## Configuration

Security features can be configured in `src/security/security_init.py`:

- Rate limiting thresholds
- Account lockout settings
- Password requirements
- CSRF protection settings

## Notes

- Rate limiting uses in-memory storage (consider Redis for production)
- Account lockout is in-memory (consider database storage for production)
- CSRF tokens are stored in Flask sessions
- Security headers are automatically added to all responses

