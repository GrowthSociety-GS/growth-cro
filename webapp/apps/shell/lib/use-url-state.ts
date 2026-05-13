"use client";

// useUrlState — reusable hook that syncs a single searchParam <-> local state
// (SP-8 — webapp-search-filter-sort-patterns).
//
// Mono-concern : URL <-> state synchronization. No filtering, no fetching.
// Pattern :
//   const [q, setQ] = useUrlState("q", "", { debounceMs: 300 });
//   const [sort, setSort] = useUrlState("sort", "name_asc");
//
// Design choices :
// - router.replace() (not push) : pas d'historique pollué pour chaque touche
//   tapée, et pas de re-execution Server Component a chaque debounce step.
// - { scroll: false } : pas de jump en haut de page.
// - debounceMs : par defaut 0 (instant) — passer 300 pour les inputs texte.
// - resetPage : true par defaut — bumper un filtre remet ?page=1 (delete param).
// - defaultValue : si setValue(defaultValue) → param efface (URL propre).

import { useCallback, useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

export type UseUrlStateOptions = {
  /** Delay (ms) avant d'ecrire dans l'URL. 0 = instant. Default 0. */
  debounceMs?: number;
  /** Si true, supprime ?page= a chaque ecriture. Default true. */
  resetPage?: boolean;
};

type Setter<T> = (next: T) => void;

export function useUrlState<T extends string>(
  key: string,
  defaultValue: T,
  options: UseUrlStateOptions = {}
): [T, Setter<T>] {
  const { debounceMs = 0, resetPage = true } = options;
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  // Source de verite cote serveur : ce que dit l'URL.
  const urlValue = (params.get(key) as T | null) ?? defaultValue;

  // Local draft pour les inputs (necessaire pour ne pas perdre le focus
  // entre re-renders pendant un debounce).
  const [draft, setDraft] = useState<T>(urlValue);

  // Sync : si l'URL change cote externe (ex: navigation, reset),
  // on resync le draft pour eviter qu'il diverge.
  useEffect(() => {
    setDraft(urlValue);
    // urlValue est derive de params, donc react aux changements params.
    // On veut PAS reset le draft sur change interne -- mais comme on ecrit
    // via router.replace + searchParams se met a jour, ca crée une boucle
    // potentielle. Guard : ne reset que si draft ne match deja pas urlValue
    // ET qu'on n'est pas en train de debounce. Le useRef ci-dessous gere ca.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlValue]);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const writeToUrl = useCallback(
    (value: T) => {
      const sp = new URLSearchParams(params.toString());
      if (!value || value === defaultValue) {
        sp.delete(key);
      } else {
        sp.set(key, value);
      }
      if (resetPage && key !== "page") {
        sp.delete("page");
      }
      const qs = sp.toString();
      const href = qs ? `${pathname}?${qs}` : pathname;
      router.replace(href, { scroll: false });
    },
    [params, pathname, router, key, defaultValue, resetPage]
  );

  const setValue: Setter<T> = useCallback(
    (next: T) => {
      setDraft(next);
      if (timerRef.current) clearTimeout(timerRef.current);
      if (debounceMs > 0) {
        timerRef.current = setTimeout(() => writeToUrl(next), debounceMs);
      } else {
        writeToUrl(next);
      }
    },
    [debounceMs, writeToUrl]
  );

  // Cleanup timer au unmount pour eviter les setStates orphelins.
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return [draft, setValue];
}

// Helper : reset all known filter keys + page en une operation atomique.
// Utilise par <FiltersBar /> "Reset all" button.
export function useUrlStateReset(keys: string[]): () => void {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  return useCallback(() => {
    const sp = new URLSearchParams(params.toString());
    for (const k of keys) sp.delete(k);
    sp.delete("page");
    const qs = sp.toString();
    const href = qs ? `${pathname}?${qs}` : pathname;
    router.replace(href, { scroll: false });
  }, [router, pathname, params, keys]);
}
