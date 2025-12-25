"""
Password strength validation module.

This module provides password strength checking to ensure users
create secure passwords.
"""

import re
from typing import List, Tuple


class PasswordValidator:
    """
    Password strength validator.
    
    Checks password against various criteria to ensure strength.
    """
    
    def __init__(self, min_length: int = 8, require_uppercase: bool = True,
                 require_lowercase: bool = True, require_digit: bool = True,
                 require_special: bool = True):
        """
        Initialize password validator with requirements.
        
        Args:
            min_length: Minimum password length
            require_uppercase: Require at least one uppercase letter
            require_lowercase: Require at least one lowercase letter
            require_digit: Require at least one digit
            require_special: Require at least one special character
        """
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special
        
        # Common weak passwords
        self.common_passwords = {
            'password', '123456', '12345678', '123456789', '1234567890',
            'qwerty', 'abc123', 'password1', 'welcome', 'letmein',
            'monkey', 'dragon', 'master', 'sunshine', 'princess',
            'football', 'iloveyou', 'admin', 'root', 'toor'
        }
    
    def validate(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not password or not isinstance(password, str):
            return False, ['Password is required']
        
        # Check length
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        
        # Check for common passwords
        if password.lower() in self.common_passwords:
            errors.append("Password is too common. Please choose a more unique password")
        
        # Check for uppercase
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check for lowercase
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check for digit
        if self.require_digit and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        # Check for special character
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for repeated characters (e.g., "aaaa")
        if re.search(r'(.)\1{3,}', password):
            errors.append("Password contains too many repeated characters")
        
        # Check for sequential characters (e.g., "1234", "abcd")
        if self._has_sequential_chars(password):
            errors.append("Password contains sequential characters")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _has_sequential_chars(self, password: str) -> bool:
        """
        Check if password contains sequential characters.
        
        Args:
            password: Password to check
            
        Returns:
            True if sequential characters found, False otherwise
        """
        if len(password) < 4:
            return False
        
        # Check for sequential digits
        for i in range(len(password) - 3):
            substr = password[i:i+4]
            if substr.isdigit():
                digits = [int(c) for c in substr]
                if all(digits[j] == digits[0] + j for j in range(4)):
                    return True
                if all(digits[j] == digits[0] - j for j in range(4)):
                    return True
        
        # Check for sequential letters
        for i in range(len(password) - 3):
            substr = password[i:i+4].lower()
            if substr.isalpha():
                ords = [ord(c) for c in substr]
                if all(ords[j] == ords[0] + j for j in range(4)):
                    return True
                if all(ords[j] == ords[0] - j for j in range(4)):
                    return True
        
        return False
    
    def calculate_strength(self, password: str) -> str:
        """
        Calculate password strength (weak, medium, strong).
        
        Args:
            password: Password to evaluate
            
        Returns:
            Strength level: 'weak', 'medium', or 'strong'
        """
        if not password:
            return 'weak'
        
        score = 0
        
        # Length score
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1
        
        # Character variety score
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        
        # Deduct for common passwords
        if password.lower() in self.common_passwords:
            score -= 3
        
        # Determine strength
        if score <= 2:
            return 'weak'
        elif score <= 5:
            return 'medium'
        else:
            return 'strong'

