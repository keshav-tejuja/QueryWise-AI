import { cva, type VariantProps } from "class-variance-authority";
import { AlertCircle, AlertTriangle, CheckCircle2 } from "lucide-react";
import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const alertVariants = cva("flex gap-3 rounded-md border p-3 text-sm", {
  variants: {
    variant: {
      destructive: "border-destructive/40 bg-destructive/10 text-destructive",
      success: "border-success/40 bg-success/10 text-success",
      warning: "border-warning/40 bg-warning/10 text-warning",
      info: "border-border bg-muted text-foreground",
    },
  },
  defaultVariants: { variant: "info" },
});

const icons = { destructive: AlertCircle, success: CheckCircle2, warning: AlertTriangle } as const;

interface AlertProps extends HTMLAttributes<HTMLDivElement>, VariantProps<typeof alertVariants> {}

export function Alert({ variant, className, children, ...props }: AlertProps) {
  const Icon = variant && variant !== "info" ? icons[variant] : null;
  return (
    <div
      role={variant === "destructive" ? "alert" : "status"}
      className={cn(alertVariants({ variant }), className)}
      {...props}
    >
      {Icon && <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />}
      <div>{children}</div>
    </div>
  );
}