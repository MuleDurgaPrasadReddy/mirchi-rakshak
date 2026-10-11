import { createFileRoute, redirect } from "@tanstack/react-router";
import { supabase } from "@/integrations/supabase/client";

export const Route = createFileRoute("/")({
  ssr: false,
  beforeLoad: async () => {
    if (typeof window === "undefined") return;
    const { data } = await supabase.auth.getSession();
    if (data.session) throw redirect({ to: "/home" });
    const seenOnboarding = window.localStorage.getItem("mr-onboarded");
    if (seenOnboarding) throw redirect({ to: "/auth" });
    throw redirect({ to: "/onboarding" });
  },
  component: () => null,
});
