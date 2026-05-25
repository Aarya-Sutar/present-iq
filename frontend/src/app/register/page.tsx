"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import api from "@/lib/api";
import { usePopup } from "@/components/popup";

export default function RegisterPage() {
  const router = useRouter();
  const { notify } = usePopup();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleRegister = async () => {
    try {
      await api.post("/auth/register", {
        full_name: fullName,
        email,
        password,
      });

      await notify({
        title: "Registration successful",
        message: "Your account is ready. You can log in now.",
        tone: "success",
        confirmLabel: "Go to login",
      });
      router.push("/login");
    } catch (error) {
      console.error(error);
      await notify({
        title: "Registration failed",
        message: "Please check the form values and try again.",
        tone: "danger",
        confirmLabel: "Try again",
      });
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-950 px-6 text-white">
      <div className="w-full max-w-md space-y-4 rounded-2xl border border-zinc-800 bg-zinc-900 p-8">
        <h1 className="text-3xl font-semibold">Register</h1>

        <input
          className="w-full rounded-lg border border-zinc-700 bg-zinc-800 p-3"
          placeholder="Full Name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
        />

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
          onClick={handleRegister}
          className="w-full rounded-lg bg-white p-3 font-medium text-black"
        >
          Register
        </button>
      </div>
    </main>
  );
}