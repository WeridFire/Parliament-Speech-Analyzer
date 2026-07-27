import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../lib/useTheme';
import { cn } from '../lib/cn';

export function ThemeToggle({ className }) {
  const { isDark, toggle } = useTheme();

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? 'Passa al tema chiaro' : 'Passa al tema scuro'}
      title={isDark ? 'Tema chiaro' : 'Tema scuro'}
      className={cn(
        'rounded-sm p-1.5 text-muted transition-colors duration-150 hover:bg-hover hover:text-ink',
        className,
      )}
    >
      {isDark ? <Sun size={16} aria-hidden="true" /> : <Moon size={16} aria-hidden="true" />}
    </button>
  );
}
