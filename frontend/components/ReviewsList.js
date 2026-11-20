"use client"; // ce composant tourne dans le navigateur

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api"; // l'outil qui envoie le badge au backend
import ReactMarkdown from "react-markdown"; // transforme le Markdown (*, **) en italique, gras...

// Transforme une date en texte lisible, ex : "vendredi 20 novembre 2026 à 18:16"
function formatDate(timestamp) {
    const date = new Date(timestamp);
    const day = date.toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
    const time = date.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
    return `${day} à ${time}`;
}

// Transforme une revue en texte simple, pour le bouton "Copier"
function reviewToText(review) {
    const articles = review.articles
        .map((a) => `- ${a.title} (${a.source}${a.date ? `, ${a.date}` : ""})\n  ${a.summary}${a.url ? `\n  ${a.url}` : ""}`)
        .join("\n\n");
    return `${review.title}\n${formatDate(review.created_at)}\n\n${review.synthesis}\n\nArticles :\n\n${articles}`;
}

// Une revue de presse : titre, date, synthèse, articles, et bouton "Copier"
function ReviewCard({ review }) {
    const [copied, setCopied] = useState(false); // vrai juste après avoir copié

    async function handleCopy() {
        await navigator.clipboard.writeText(reviewToText(review)); // copie dans le presse-papiers
        setCopied(true);
        setTimeout(() => setCopied(false), 2000); // le message "Copié" disparaît après 2 secondes
    }

    return (
        <article className="rounded-2xl bg-white p-8 shadow-sm">
            <div className="flex items-start justify-between gap-4">
                <div>
                    <h2 className="font-semibold uppercase">{review.title}</h2>
                    <p className="mt-1 text-sm text-gray-500">📅 {formatDate(review.created_at)}</p>
                </div>
                <button
                    type="button"
                    onClick={handleCopy}
                    className="shrink-0 rounded-lg bg-neutral-900 px-4 py-2 text-sm text-white hover:bg-neutral-700"
                >
                    {copied ? "Copié ✅" : "Copier"}
                </button>
            </div>

            <div className="prose prose-sm mt-6 max-w-none">
                <ReactMarkdown>{review.synthesis}</ReactMarkdown>
            </div>

            {review.articles.length > 0 && (
                <ul className="mt-6 space-y-4">
                    {review.articles.map((article, index) => (
                        <li key={index} className="border-l-4 border-violet-200 pl-4 text-sm">
                            <p className="font-semibold">{article.title}</p>
                            <p className="text-gray-500">
                                {article.source}
                                {article.date && ` · ${article.date}`}
                            </p>
                            <p className="mt-1 text-gray-800">{article.summary}</p>
                            {article.url && (
                                <a
                                    href={article.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="mt-1 inline-block text-violet-600 underline"
                                >
                                    Lire l&apos;article
                                </a>
                            )}
                        </li>
                    ))}
                </ul>
            )}
        </article>
    );
}

// La page des revues de presse : toutes mes revues (GET /reviews)
export default function ReviewsList() {
    const [reviews, setReviews] = useState([]); // la liste des revues
    const [isLoading, setIsLoading] = useState(true); // vrai pendant le chargement
    const [error, setError] = useState(""); // un message d'erreur

    // Au chargement : on récupère toutes mes revues
    useEffect(() => {
        apiFetch("/reviews")
            .then((data) => setReviews(data))
            .catch((err) => setError(err.message))
            .finally(() => setIsLoading(false));
    }, []);

    return (
        <section aria-label="Revues de presse" className="flex-1 overflow-y-auto bg-[#e6e6f0] p-8">
            <div className="mx-auto max-w-4xl">
                <h1 className="text-2xl">Revues de Presse</h1>
                <p className="mt-1 text-sm text-gray-500">Consultez et gérez vos revues de presse générées par l&apos;IA</p>

                {isLoading && <p className="mt-6 text-gray-500">Chargement des revues...</p>}
                {error && <p role="alert" className="mt-6 text-red-600">{error}</p>}
                {!isLoading && !error && reviews.length === 0 && (
                    <p className="mt-6 text-gray-500">
                        Aucune revue pour l&apos;instant. Ouvrez une discussion et cliquez sur « Générer une revue de presse ».
                    </p>
                )}

                <div className="mt-6 space-y-6">
                    {reviews.map((review) => (
                        <ReviewCard key={review.chat_id} review={review} />
                    ))}
                </div>
            </div>
        </section>
    );
}