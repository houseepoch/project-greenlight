"use client";

import * as ToastPrimitive from "@radix-ui/react-toast";
import { X, CheckCircle, XCircle, AlertCircle, Info, Bell } from "lucide-react";
import { cn } from "@/lib/utils";
import { create } from "zustand";

// Toast types
export type ToastType = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  title: string;
  description?: string;
  type: ToastType;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// Toast store
interface ToastStore {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, "id">) => string;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  addToast: (toast) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    set((state) => ({
      toasts: [...state.toasts, { ...toast, id }],
    }));
    return id;
  },
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
  clearToasts: () => set({ toasts: [] }),
}));

// Helper function for easy toast creation
export const toast = {
  success: (title: string, description?: string, action?: Toast["action"]) =>
    useToastStore.getState().addToast({ title, description, type: "success", action }),
  error: (title: string, description?: string, action?: Toast["action"]) =>
    useToastStore.getState().addToast({ title, description, type: "error", action }),
  warning: (title: string, description?: string, action?: Toast["action"]) =>
    useToastStore.getState().addToast({ title, description, type: "warning", action }),
  info: (title: string, description?: string, action?: Toast["action"]) =>
    useToastStore.getState().addToast({ title, description, type: "info", action }),
};

// Icon mapping
const getIcon = (type: ToastType) => {
  switch (type) {
    case "success":
      return <CheckCircle className="h-5 w-5 text-green-400" />;
    case "error":
      return <XCircle className="h-5 w-5 text-red-400" />;
    case "warning":
      return <AlertCircle className="h-5 w-5 text-yellow-400" />;
    case "info":
      return <Info className="h-5 w-5 text-blue-400" />;
  }
};

// Toast item component
function ToastItem({ toast: t, onRemove }: { toast: Toast; onRemove: () => void }) {
  return (
    <ToastPrimitive.Root
      className={cn(
        "group pointer-events-auto relative flex w-full items-center justify-between space-x-4 overflow-hidden rounded-lg border p-4 pr-8 shadow-lg transition-all",
        "data-[swipe=cancel]:translate-x-0 data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[swipe=move]:transition-none",
        "data-[state=open]:animate-in data-[state=closed]:animate-out data-[swipe=end]:animate-out data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full data-[state=open]:slide-in-from-top-full",
        t.type === "success" && "border-green-500/30 bg-green-500/10",
        t.type === "error" && "border-red-500/30 bg-red-500/10",
        t.type === "warning" && "border-yellow-500/30 bg-yellow-500/10",
        t.type === "info" && "border-blue-500/30 bg-blue-500/10"
      )}
      duration={t.duration || 5000}
      onOpenChange={(open) => {
        if (!open) onRemove();
      }}
    >
      <div className="flex items-start gap-3">
        {getIcon(t.type)}
        <div className="grid gap-1">
          <ToastPrimitive.Title className="text-sm font-semibold text-foreground">
            {t.title}
          </ToastPrimitive.Title>
          {t.description && (
            <ToastPrimitive.Description className="text-sm text-muted-foreground">
              {t.description}
            </ToastPrimitive.Description>
          )}
        </div>
      </div>
      {t.action && (
        <ToastPrimitive.Action
          className="inline-flex h-8 shrink-0 items-center justify-center rounded-md border border-border bg-transparent px-3 text-sm font-medium transition-colors hover:bg-secondary focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
          altText={t.action.label}
          onClick={t.action.onClick}
        >
          {t.action.label}
        </ToastPrimitive.Action>
      )}
      <ToastPrimitive.Close
        className="absolute right-2 top-2 rounded-md p-1 text-foreground/50 opacity-0 transition-opacity hover:text-foreground focus:opacity-100 focus:outline-none focus:ring-2 group-hover:opacity-100"
        onClick={onRemove}
      >
        <X className="h-4 w-4" />
      </ToastPrimitive.Close>
    </ToastPrimitive.Root>
  );
}

// Toast provider component
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const { toasts, removeToast } = useToastStore();

  return (
    <ToastPrimitive.Provider swipeDirection="right">
      {children}
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onRemove={() => removeToast(t.id)} />
      ))}
      <ToastPrimitive.Viewport className="fixed top-0 right-0 z-[100] flex max-h-screen w-full flex-col-reverse p-4 sm:top-auto sm:bottom-0 sm:right-0 sm:flex-col md:max-w-[420px]" />
    </ToastPrimitive.Provider>
  );
}
