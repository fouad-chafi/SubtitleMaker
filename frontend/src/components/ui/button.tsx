import { type VariantProps, cva } from 'class-variance-authority';
import type { ButtonHTMLAttributes, forwardRef, ForwardRefRenderFunction } from 'react';
import { cn } from '../../lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-white shadow hover:bg-primary/90',
        destructive: 'bg-error text-white shadow-sm hover:bg-error/90',
        outline: 'border border-neutral-200 bg-transparent shadow-sm hover:bg-neutral-100 hover:text-neutral-900',
        secondary: 'bg-secondary text-white shadow-sm hover:bg-secondary/80',
        ghost: 'hover:bg-neutral-100 hover:text-neutral-900',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-10 rounded-md px-8',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const ButtonRender: ForwardRefRenderFunction<HTMLButtonElement, ButtonProps> = (
  { className, variant, size, ...props },
  ref
) => {
  return (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      {...props}
    />
  );
};

const Button = forwardRef(ButtonRender);
Button.displayName = 'Button';

export { Button, buttonVariants };
