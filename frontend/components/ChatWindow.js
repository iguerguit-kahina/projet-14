"use client"; // ce composant tourne dans le navigateur

import { useEffect, useRef, useState } from "react";
import { apiFetch } from "@/lib/api"; // l'outil qui envoie le badge au backend
import ReactMarkdown from "react-markdown"; // transforme le Markdown en vrais titres, gras, listes

// Transforme une date en heure lisible, ex : "10:31"
function formatTime(timestamp) {
    return new Date(timestamp).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

// L'écran d'accueil (quand aucune discussion n'est ouverte), comme sur la maquette
function WelcomeCard() {
    return (
        <div className="mx-auto mt-16 max-w-md rounded-2xl bg-white p-10 text-center shadow-sm">
            <p className="text-5xl" aria-hidden="true">🤖</p>
            <h2 className="mt-4 text-2xl text-violet-600">Assistant Revue de Presse IA</h2>
            <p className="mt-4 text-sm text-gray-500">
                Posez-moi des questions sur l&apos;actualité récente ou demandez-moi de générer une revue
                de presse sur un sujet spécifique.
            </p>
            <p className="mt-6 text-sm font-semibold text-gray-600">Exemples :</p>
            <ul className="mt-2 space-y-1 text-sm text-gray-500">
                <li>« Quelles sont les dernières nouvelles en politique ? »</li>
                <li>« Génère une revue de presse sur la technologie »</li>
                <li>« Résume l&apos;actualité économique de la semaine »</li>
            </ul>
        </div>
    );
}

// Une bulle de message : à droite en noir (utilisateur), à gauche en gris clair (IA)
function MessageBubble({ message }) {
    const isUser = message.role === "user";
    return (
        <li className={`flex items-start gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
            <span
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm ${isUser ? "bg-neutral-900 text-white" : "bg-white"
                    }`}
                aria-hidden="true"
            >
                {isUser ? "👤" : "🤖"}
            </span>
            <div
                className={`max-w-xl rounded-xl px-4 py-3 text-sm ${isUser ? "bg-neutral-800 text-white" : "bg-gray-100 text-gray-900"
                    }`}
            >
                <span className="sr-only">{isUser ? "Vous :" : "Assistant :"}</span>
                {isUser ? (
                    // Message de l'utilisateur : texte simple
                    <p className="whitespace-pre-wrap">{message.content}</p>
                ) : (
                    // Réponse de l'IA : on affiche le Markdown joliment ("prose" = style des titres et listes)
                    <div className="prose prose-sm max-w-none">
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                )}
                <p className={`mt-2 text-xs ${isUser ? "text-gray-300" : "text-gray-500"}`}>
                    {formatTime(message.timestamp)}
                </p>
            </div>
        </li>
    );
}

// La zone de chat
// 🆕 onChatCreated : prévient la page quand une nouvelle discussion est créée
export default function ChatWindow({ chatId, onChatCreated }) {
    const [messages, setMessages] = useState([]); // les messages de la discussion
    const [isLoading, setIsLoading] = useState(false); // vrai pendant le chargement
    const [error, setError] = useState(""); // un message d'erreur
    const [input, setInput] = useState(""); // 🆕 le texte en train d'être écrit
    const [isSending, setIsSending] = useState(false); // 🆕 vrai pendant que l'IA réfléchit
    const bottomRef = useRef(null); // 🆕 un repère tout en bas, pour y faire défiler

    // À chaque changement de discussion, on charge ses messages (GET /chats/{id})
    useEffect(() => {
        if (!chatId) {
            setMessages([]); // aucune discussion ouverte → écran d'accueil
            return;
        }
        setIsLoading(true);
        setError("");
        apiFetch(`/chats/${chatId}`)
            .then((data) => setMessages(data.messages))
            .catch((err) => setError(err.message))
            .finally(() => setIsLoading(false));
    }, [chatId]);

    // 🆕 À chaque nouveau message, on fait défiler jusqu'en bas
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isSending]);

    // 🆕 Envoi d'un message
    async function handleSend(event) {
        event.preventDefault(); // empêche la page de se recharger
        const content = input.trim();
        if (!content || isSending) return; // rien à envoyer, ou déjà en cours

        setError("");
        setInput("");
        setIsSending(true);

        // 1. On affiche tout de suite le message de l'utilisateur
        setMessages((previous) => [
            ...previous,
            { role: "user", content, timestamp: new Date().toISOString() },
        ]);

        try {
            // 2. Nouvelle discussion ? On la crée d'abord (POST /chats)
            let currentChatId = chatId;
            if (!currentChatId) {
                const created = await apiFetch("/chats", { method: "POST" });
                currentChatId = created.id;
            }

            // 3. On envoie le message à l'IA (POST /chats/{id}/messages)
            const data = await apiFetch(`/chats/${currentChatId}/messages`, {
                method: "POST",
                body: JSON.stringify({ content }),
            });

            // 4. On affiche la réponse de l'IA
            setMessages((previous) => [
                ...previous,
                { role: "assistant", content: data.answer, timestamp: new Date().toISOString() },
            ]);

            // 5. Si la discussion vient d'être créée, on prévient la page (pour la liste à gauche)
            if (!chatId) onChatCreated(currentChatId);
        } catch (err) {
            setError(err.message);
            setInput(content); // on remet le message dans la zone, pour pouvoir réessayer
        } finally {
            setIsSending(false);
        }
    }

    // 🆕 Entrée = envoyer ; Maj + Entrée = aller à la ligne
    function handleKeyDown(event) {
        if (event.key === "Enter" && !event.shiftKey) {
            handleSend(event);
        }
    }

    return (
        <div className="flex h-full flex-1 flex-col">
            {/* Les messages */}
            <section aria-label="Discussion" className="flex-1 overflow-y-auto bg-[#e6e6f0] p-8">
                {isLoading && <p className="text-gray-500">Chargement de la discussion...</p>}

                {!isLoading && messages.length === 0 && <WelcomeCard />}

                {messages.length > 0 && (
                    <ul className="mx-auto w-full max-w-3xl space-y-6">
                        {messages.map((message, index) => (
                            <MessageBubble key={index} message={message} />
                        ))}
                    </ul>
                )}

                {/* 🆕 Pendant que l'IA réfléchit (annoncé aux lecteurs d'écran) */}
                {isSending && (
                    <p role="status" className="mx-auto mt-6 max-w-3xl text-sm text-gray-500">
                        L&apos;IA réfléchit...
                    </p>
                )}

                {error && (
                    <p role="alert" className="mx-auto mt-6 max-w-3xl text-sm text-red-600">
                        {error}
                    </p>
                )}

                <div ref={bottomRef} />
            </section>

            {/* 🆕 La zone d'écriture, en bas */}
            <form onSubmit={handleSend} className="flex items-end gap-3 border-t border-gray-200 bg-white p-4">
                <label htmlFor="message" className="sr-only">
                    Votre message
                </label>
                <textarea
                    id="message"
                    rows={2}
                    value={input}
                    onChange={(event) => setInput(event.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Tapez votre message ici..."
                    className="flex-1 resize-none rounded-lg bg-gray-100 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-violet-600"
                />
                <button
                    type="submit"
                    disabled={!input.trim() || isSending}
                    aria-label="Envoyer le message"
                    className="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-600 text-white hover:bg-violet-700 disabled:bg-gray-300"
                >
                    ➤
                </button>
            </form>
        </div>
    );
}