"use client"; // cette page tourne dans le navigateur (local storage, clics...)

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import Sidebar from "@/components/Sidebar"; // la colonne de gauche
import { apiFetch } from "@/lib/api"; // l'outil qui envoie le badge au backend
import ChatWindow from "@/components/ChatWindow"; // la zone de chat

export default function HomePage() {
  const router = useRouter();

  // Les "états" de la page
  const [isReady, setIsReady] = useState(false); // vrai quand on a vérifié le badge
  const [chats, setChats] = useState([]); // la liste des discussions
  const [selectedChatId, setSelectedChatId] = useState(null); // la discussion ouverte (null = accueil)
  const [error, setError] = useState(""); // un message d'erreur à afficher

  // Charge la liste des discussions depuis le backend (route GET /chats)
  async function loadChats() {
    try {
      const data = await apiFetch("/chats");
      setChats(data);
    } catch (err) {
      setError(err.message);
    }
  }

  // Au chargement de la page : on vérifie le badge, puis on charge les discussions
  useEffect(() => {
    if (!localStorage.getItem("token")) {
      router.replace("/login"); // pas de badge → page de connexion
      return;
    }
    setIsReady(true);
    loadChats();
  }, [router]);

  // Déconnexion : on efface le badge et on retourne à la connexion
  function handleLogout() {
    localStorage.removeItem("token");
    router.push("/login");
  }

  // Pendant la vérification du badge
  if (!isReady) {
    return <p className="p-8 text-gray-500">Chargement...</p>;
  }

  return (
    <div className="flex h-screen">
      {/* La colonne de gauche */}
      <Sidebar
        chats={chats}
        selectedChatId={selectedChatId}
        onSelectChat={setSelectedChatId}
        onNewChat={() => setSelectedChatId(null)}
        onLogout={handleLogout}
      />

      {/* La zone de droite (le chat arrive à l'étape suivante) */}
      {/* La zone de droite (le chat arrive à l'étape suivante) */}
      {/* La zone de droite : le chat */}
      <main className="flex flex-1 flex-col">
        {error && <p role="alert" className="p-4 text-red-600">{error}</p>}
        <ChatWindow
          chatId={selectedChatId}
          onChatCreated={(newChatId) => {
            setSelectedChatId(newChatId); // on ouvre la nouvelle discussion
            loadChats(); // on recharge la liste à gauche
          }}
        />
      </main>
    </div>
  );
}