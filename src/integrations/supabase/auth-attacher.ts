import { createMiddleware } from '@tanstack/react-start'
import { supabase } from './client'
import { auth } from '@/lib/firebase'

// Must be registered as a global `functionMiddleware` in `src/start.ts`; otherwise
// the browser never attaches the bearer token to serverFn RPCs.
export const attachSupabaseAuth = createMiddleware({ type: 'function' }).client(
  async ({ next }) => {
    let token: string | undefined;
    try {
      const { data } = await supabase.auth.getSession();
      token = data.session?.access_token;
    } catch {}

    if (!token && auth?.currentUser) {
      try {
        token = await auth.currentUser.getIdToken();
      } catch (e) {
        console.warn('[Auth Attacher] Could not get Firebase token:', e);
      }
    }

    return next({
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
  },
);

