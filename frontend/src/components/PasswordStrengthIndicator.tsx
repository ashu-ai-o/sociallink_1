import React from 'react';

interface PasswordStrengthIndicatorProps {
  password: string;
}

export const PasswordStrengthIndicator: React.FC<PasswordStrengthIndicatorProps> = ({
  password,
}) => {
  const calculateStrength = (pwd: string): number => {
    let strength = 0;
    
    if (pwd.length >= 8) strength += 1;
    if (pwd.length >= 12) strength += 1;
    if (/[a-z]/.test(pwd)) strength += 1;
    if (/[A-Z]/.test(pwd)) strength += 1;
    if (/\d/.test(pwd)) strength += 1;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) strength += 1;
    
    return strength;
  };
  
  const getStrengthText = (strength: number): string => {
    if (strength < 3) return 'Weak';
    if (strength < 5) return 'Medium';
    return 'Strong';
  };
  
  const getStrengthColor = (strength: number): string => {
    if (strength < 3) return 'bg-red-500';
    if (strength < 5) return 'bg-yellow-500';
    return 'bg-green-500';
  };
  
  const strength = calculateStrength(password);
  const strengthText = getStrengthText(strength);
  const strengthColor = getStrengthColor(strength);
  const widthPercentage = (strength / 6) * 100;
  
  if (!password) return null;
  
  return (
    <div className="mt-2">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-gray-600">Password Strength</span>
        <span className="text-xs font-medium">{strengthText}</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${strengthColor} transition-all duration-300`}
          style={{ width: `${widthPercentage}%` }}
        />
      </div>
      <ul className="mt-2 text-xs text-gray-600 space-y-1">
        <li className={password.length >= 8 ? 'text-green-600' : ''}>
          ✓ At least 8 characters
        </li>
        <li className={/[A-Z]/.test(password) ? 'text-green-600' : ''}>
          ✓ One uppercase letter
        </li>
        <li className={/[a-z]/.test(password) ? 'text-green-600' : ''}>
          ✓ One lowercase letter
        </li>
        <li className={/\d/.test(password) ? 'text-green-600' : ''}>
          ✓ One number
        </li>
        <li className={/[!@#$%^&*(),.?":{}|<>]/.test(password) ? 'text-green-600' : ''}>
          ✓ One special character
        </li>
      </ul>
    </div>
  );
};

