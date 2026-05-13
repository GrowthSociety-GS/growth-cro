"use client";
import { useMemo } from "react";
import { getBrowserSupabase } from "@growthcro/data";

export function useSupabase() {
  return useMemo(() => getBrowserSupabase(), []);
}
