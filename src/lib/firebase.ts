import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getAnalytics, isSupported } from "firebase/analytics";

const firebaseConfig = {
  apiKey: "AIzaSyCHEsZ81dvN4aPr8K8VXHUOYtDCc2bm6Bc",
  authDomain: "mirchi-rakshak-ai.firebaseapp.com",
  projectId: "mirchi-rakshak-ai",
  storageBucket: "mirchi-rakshak-ai.firebasestorage.app",
  messagingSenderId: "282241765076",
  appId: "1:282241765076:web:8c07fba0bc321c7657b541",
  measurementId: "G-5FEBSY9603"
};

export const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();

if (typeof window !== "undefined") {
  isSupported().then((supported) => {
    if (supported) {
      getAnalytics(app);
    }
  });
}
