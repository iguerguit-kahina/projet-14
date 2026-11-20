"use client"; // cette page tourne dans le navigateur (local storage, clics...)

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import Sidebar from "@/components/Sidebar"; // la colonne de gauche
import { apiFetch } from "@/lib/api"; // l'outil qui envoie le badge au backend
import ChatWindow from "@/components/ChatWindow"; // la zone de chat
import ReviewsList from "@/components/ReviewsList"; // 🆕 la page des revues de presse

// 🆕 Un onglet en haut de la zone de droite ("Chat" ou "Revue de presse")
function TabButton({ isActive, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={isActive}
      className={`rounded-lg px-4 py-2 text-sm ${isActive ? "bg-violet-600 text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
        }`}
    >
      {children}
    </button>
  );
}

export default function HomePage() {
  const router = useRouter();

  // Les "états" de la page
  const [isReady, setIsReady] = useState(false); // vrai quand on a vérifié le badge
  const [chats, setChats] = useState([]); // la liste des discussions
  const [selectedChatId, setSelectedChatId] = useState(null); // la discussion ouverte (null = accueil)
  const [error, setError] = useState(""); // un message d'erreur à afficher
  const [activeTab, setActiveTab] = useState("chat"); // 🆕 l'onglet affiché : "chat" ou "reviews"

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

  // 🆕 Ouvrir une discussion : on revient aussi sur l'onglet "Chat"
  function handleSelectChat(chatId) {
    setSelectedChatId(chatId);
    setActiveTab("chat");
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
        onSelectChat={handleSelectChat}
        onNewChat={() => handleSelectChat(null)}
        onLogout={handleLogout}
      />

      {/* La zone de droite */}
      <main className="flex flex-1 flex-col">
        {/* 🆕 Les onglets, comme sur la maquette */}
        <nav aria-label="Navigation" className="flex gap-2 border-b border-gray-200 bg-white px-6 py-3">
          <TabButton isActive={activeTab === "chat"} onClick={() => setActiveTab("chat")}>
            💬 Chat
          </TabButton>
          <TabButton isActive={activeTab === "reviews"} onClick={() => setActiveTab("reviews")}>
            📄 Revue de presse
          </TabButton>
        </nav>

        {error && <p role="alert" className="p-4 text-red-600">{error}</p>}

        {/* 🆕 On affiche le chat OU la page des revues, selon l'onglet */}
        {activeTab === "chat" ? (
          <ChatWindow
            chatId={selectedChatId}
            onChatCreated={(newChatId) => {
              setSelectedChatId(newChatId); // on ouvre la nouvelle discussion
              loadChats(); // on recharge la liste à gauche
            }}
          />
        ) : (
          <ReviewsList />
        )}
      </main>
    </div>
  );
}