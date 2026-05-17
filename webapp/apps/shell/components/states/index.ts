// states/index.ts — barrel export for canonical state components (B2 / #73).
// Consumers (C1, D/E/F/G loaders): `import { EmptyState } from "@/components/states";`

export { EmptyState } from "./EmptyState";
export { LoadingSkeleton } from "./LoadingSkeleton";
export { BlockedState } from "./BlockedState";
export { WorkerOfflineState } from "./WorkerOfflineState";
export { ErrorBoundary } from "./ErrorBoundary";
