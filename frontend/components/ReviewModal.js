"use client"; // ce composant tourne dans le navigateur

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api"; // l'outil qui envoie le badge au backend

// La petite fenêtre (modale) pour générer une revue de presse, comme sur la maquette
// chatId : la discussion à résumer ; onClose : fermer la modale ; onGenerated : prévenir quand c'est fini
export default function ReviewModal({ chatId, onClose, onGenerated }) {
    const [topic, setTopic] = useState(""); // le thème écrit par l'utilisateur
    const [isGenerating, setIsGenerating] = useState(false); // vrai pendant que l'IA rédige
    const [error, setError] = useState(""); // un message d'erreur

    // Touche Échap = fermer la modale (sauf pendant la génération)
    useEffect(() => {
        function handleKeyDown(event) {
            if (event.key === "Escape" && !isGenerating) onClose();
        }
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [isGenerating, onClose]);

    // Clic sur "Générer" : on demande la revue au backend (POST /chats/{id}/review)
    async function handleSubmit(event) {
        event.preventDefault(); // empêche la page de se recharger
        const cleanTopic = topic.trim();
        if (!cleanTopic || isGenerating) return;

        setError("");
        setIsGenerating(true);
        try {
            const review = await apiFetch(`/chats/${chatId}/review`, {
                method: "POST",
                body: JSON.stringify({ topic: cleanTopic }),
            });
            onGenerated(review); // on prévient ChatWindow que la revue est prête
        } catch (err) {
            setError(err.message);
        } finally {
            setIsGenerating(false);
        }
    }

    return (
        // Le fond gris transparent, par-dessus toute la page
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div
                role="dialog"
                aria-modal="true"
                aria-labelledby="review-modal-title"
                className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg"
            >
                <div className="flex justify-end">
                    <button
                        type="button"
                        onClick={onClose}
                        disabled={isGenerating}
                        className="text-xs text-gray-500 hover:text-gray-800 disabled:opacity-50"
                    >
                        Fermer
                    </button>
                </div>

                <h2 id="review-modal-title" className="text-center text-lg font-semibold">
                    Générer une revue de presse
                </h2>
                <p className="mt-1 text-center text-sm text-gray-500">
                    Donner un titre à votre revue de presse
                </p>

                <form onSubmit={handleSubmit} className="mt-6">
                    <label htmlFor="review-topic" className="block text-sm">
                        Thème de la revue de presse
                    </label>
                    <input
                        id="review-topic"
                        type="text"
                        autoFocus
                        value={topic}
                        onChange={(event) => setTopic(event.target.value)}
                        placeholder="Ex : passoires thermiques"
                        className="mt-2 w-full rounded-lg bg-gray-100 px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-violet-600"
                    />

                    {error && (
                        <p role="alert" className="mt-3 text-sm text-red-600">
                            {error}
                        </p>
                    )}

                    <button
                        type="submit"
                        disabled={!topic.trim() || isGenerating}
                        className="mt-4 w-full rounded-lg bg-neutral-900 py-2 text-sm text-white hover:bg-neutral-700 disabled:bg-gray-300"
                    >
                        {isGenerating ? "Génération en cours..." : "Générer"}
                    </button>
                </form>
            </div>
        </div>
    );
}