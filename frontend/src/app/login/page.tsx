"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import api from "@/lib/api";
import { usePopup } from "@/components/popup";
import { useAuthStore } from "@/store/useAuthStore";

export default function LoginPage() {
  const router = useRouter();
  const { notify } = usePopup();
  const setToken = useAuthStore((state) => state.setToken);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async () => {
    try {
      const response = await api.post("/auth/login", {
        email,
        password,
      });

      setToken(response.data.access_token);

      await notify({
        title: "Login successful",
        message: "You are now signed in and ready to continue.",
        tone: "success",
        confirmLabel: "Continue",
      });
      router.push("/dashboard");
    } catch (error) {
      console.error(error);
      await notify({
        title: "Login failed",
        message: "Check your email and password, then try again.",
        tone: "danger",
        confirmLabel: "Try again",
      });
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-950 px-6 text-white">
      <div className="w-full max-w-md space-y-4 rounded-2xl border border-zinc-800 bg-zinc-900 p-8">
        <h1 className="text-3xl font-semibold">Login</h1>

        <input
          className="w-full rounded-lg border border-zinc-700 bg-zinc-800 p-3"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          type="password"
          className="w-full rounded-lg border border-zinc-700 bg-zinc-800 p-3"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button
          onClick={handleLogin}
          className="w-full rounded-lg bg-white p-3 font-medium text-black"
        >
          Login
        </button>
      </div>
    </main>
  );
}