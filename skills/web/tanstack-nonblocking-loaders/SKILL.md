---
name: tanstack-nonblocking-loaders
description: Make TanStack Start/Router navigations instant by turning blocking route loaders into non-blocking React Query cache warm-ups. Use when adding or editing a route, loader, or beforeLoad in a TanStack Start/Router app that uses React Query or TanStack DB, when connecting a loader to a server function, when configuring the router or QueryClient (preload, staleTime), or when diagnosing slow/dead clicks, missing pending UI, refetch on back-navigation, or duplicate server-fn calls per navigation.
---

# Non-blocking loaders in TanStack Start

Navigations feel dead when loaders await server functions. The fix: loaders
only *warm* the React Query cache; components own fetching, loading, and
error UI. Navigation commits immediately.

## Symptoms this fixes

- Click → nothing happens for hundreds of ms, then the page swaps.
- Route `pendingComponent` never visibly renders.
- Back-navigation to an already-visited route refetches everything.
- The same server fn fires 2–3× per navigation (hover preload + loader +
  component/collection refetch).
- `beforeLoad` doing auth/context work re-runs a server round trip on every
  navigation in the subtree.

## The pattern

1. **Share query options.** Export a `queryOptions`-shaped factory next to
   whatever consumes it (component `useQuery` or TanStack DB collection), and
   use it in both the loader and the consumer — same cache entry, in-flight
   fetches dedupe:

   ```ts
   export function itemsQueryOptions(id: string) {
     return {
       queryKey: ["items", id],
       retry: 1, // permanent "not found" errors shouldn't retry for ~8s
       queryFn: async () => {
         const result = await loadItems({ data: { id } })
         if (!result) throw new Error("Not accessible")
         return result
       },
     }
   }
   ```

2. **Loader = fire-and-forget prefetch.** Never `await` data; never
   `setQueryData` from an awaited fetch:

   ```ts
   loader: ({ params, context }) => {
     // Skip during SSR when the consumer is ClientOnly and nothing
     // dehydrates the server-side cache — the fetch would be wasted.
     if (typeof document === "undefined") return
     void context.queryClient.prefetchQuery(itemsQueryOptions(params.id))
   },
   ```

3. **QueryClient needs `staleTime > 0`** (e.g. 60s) or every seed is
   refetched instantly and every revisit refetches:

   ```ts
   new QueryClient({ defaultOptions: { queries: { staleTime: 60_000 } } })
   ```

4. **Hover preloading comes free.** `defaultPreload: "intent"` runs the
   loader on hover, which now warms the same cache entry. Do NOT set
   `defaultPreloadStaleTime: 0` — that refires a full fetch on every hover.

5. **`beforeLoad` context goes through `ensureQueryData`** so it stops
   re-fetching per navigation. Use `retry: false` when the fn can throw a
   `redirect()` — otherwise React Query retries the redirect 3 times:

   ```ts
   beforeLoad: async ({ context }) =>
     await context.queryClient.ensureQueryData({
       queryKey: ["dashboard"],
       queryFn: () => loadDashboard(),
       retry: false,
     }),
   ```

6. **Move 404s into the component.** A non-blocking loader can't throw
   `notFound()`. The consumer renders an inline "isn't available" state on
   query error. TanStack DB gotcha: on queryFn error, query-db-collection
   marks the collection *ready with zero rows* — `useLiveQuery().isError`
   stays false. Read `collection.utils.isError` instead:

   ```ts
   if (rows.length === 0 && collection.utils.isError) return <Unavailable />
   ```

## Verify

Drive the app and check: navigation commits in tens of
ms with a visible loading state; revisiting a route makes **zero** network
calls; each cold navigation fires each server fn
exactly once; a bad deep link shows the inline error, not an empty state.
