import { type ReactNode } from 'react';
import clsx from 'clsx';

interface ButtonProps {
  children: ReactNode;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  variant?: 'primary' | 'secondary' | 'danger' | 'icon';
  disabled?: boolean;
  className?: string;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  size?: 'sm' | 'md' | 'lg';
  title?: string;
}

export default function Button({
  children,
  onClick,
  type = 'button',
  variant = 'primary',
  disabled = false,
  className = '',
  icon,
  iconPosition = 'left',
  fullWidth = false,
  size = 'md',
  title,
}: ButtonProps) {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  const variantClasses = {
    primary: 'border border-transparent text-white bg-gray-900 hover:bg-gray-800 disabled:bg-gray-400 disabled:cursor-not-allowed focus:ring-gray-900',
    secondary: 'border border-gray-300 text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed focus:ring-gray-500',
    danger: 'border border-transparent text-white bg-red-600 hover:bg-red-700 disabled:bg-red-400 disabled:cursor-not-allowed focus:ring-red-500',
    icon: 'border border-transparent text-gray-600 hover:text-gray-900 disabled:text-gray-400 disabled:cursor-not-allowed focus:ring-gray-500 p-2',
  };

  const classes = clsx(
    baseClasses,
    sizeClasses[size],
    variantClasses[variant],
    {
      'w-full': fullWidth,
    },
    className
  );

  const iconElement = icon && (
    <span className={iconPosition === 'left' ? 'mr-2' : 'ml-2'}>
      {icon}
    </span>
  );

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={classes}
      title={title}
    >
      {iconPosition === 'left' && iconElement}
      {children}
      {iconPosition === 'right' && iconElement}
    </button>
  );
}

