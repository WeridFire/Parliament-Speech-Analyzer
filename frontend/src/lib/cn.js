import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge conditional class names, letting later Tailwind utilities win over
 * earlier ones of the same kind. This is what lets a primitive ship sensible
 * defaults that a caller can override without `!important` or specificity wars:
 *
 *   <Card className="p-0" />   // the caller's p-0 beats Card's built-in p-5
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
