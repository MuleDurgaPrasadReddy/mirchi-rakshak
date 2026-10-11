import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { auth } from "@/lib/firebase";
import { onAuthStateChanged } from "firebase/auth";
import { supabase } from "@/integrations/supabase/client";

export const Route = createFileRoute("/_authenticated")({
  ssr: false,
  beforeLoad: async () => {
    const firebaseUser = await new Promise((resolve) => {
      if (auth.currentUser) {
        resolve(auth.currentUser);
        return;
      }
      const unsubscribe = onAuthStateChanged(
        auth,
        (u) => {
          unsubscribe();
          resolve(u);
        },
        () => {
          resolve(null);
        }
      );
    });

    if (firebaseUser) return { user: firebaseUser };

    try {
      const { data } = await supabase.auth.getUser();
      if (data?.user) return { user: data.user };
    } catch (e) {
      console.warn("Supabase auth check fallback:", e);
    }

    throw redirect({ to: "/auth" });
  },
  component: () => <Outlet />,
});
