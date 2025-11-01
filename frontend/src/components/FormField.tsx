import { type ChangeEvent } from 'react';

interface FormFieldProps {
  label: string;
  type?: 'text' | 'url' | 'number';
  value: string | number;
  onChange: (value: string | number) => void;
  required?: boolean;
  disabled?: boolean;
  placeholder?: string;
  min?: string;
  step?: string;
}

export default function FormField({
  label,
  type = 'text',
  value,
  onChange,
  required = false,
  disabled = false,
  placeholder,
  min,
  step,
}: FormFieldProps) {
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    let newValue: string | number = e.target.value;
    
    if (type === 'number') {
      newValue = step ? parseFloat(e.target.value) : parseInt(e.target.value);
    } else if (type === 'url' && typeof newValue === 'string' && newValue) {
      // Auto-prepend https:// if no protocol is specified
      if (!newValue.match(/^https?:\/\//i)) {
        newValue = 'https://' + newValue;
      }
    }
    
    onChange(newValue);
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700">
        {label} {required && '*'}
      </label>
      <input
        type={type}
        value={value}
        onChange={handleChange}
        disabled={disabled}
        required={required}
        placeholder={placeholder}
        min={min}
        step={step}
        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2 disabled:bg-gray-100"
      />
    </div>
  );
}

