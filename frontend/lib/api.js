// L'adresse du backend, lue dans le fichier .env.local
const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Outil pour envoyer une demande au backend, avec le badge.
// path = la route (ex : "/chats"), options = la méthode, le contenu...
export async function apiFetch(path, options = {}) {
    // 1. On reprend le badge rangé dans le local storage
    const token = localStorage.getItem("token");

    // 2. On envoie la demande, avec le badge dans l'en-tête
    const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
            ...options.headers,
        },
    });

    // 3. Badge manquant ou expiré → on l'efface et on renvoie vers la connexion
    if (response.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/login";
        throw new Error("Session expirée");
    }

    // 4. Autre erreur → on la signale, avec le message du backend s'il y en a un
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "Une erreur est survenue.");
    }

    // 5. Tout est bon → on renvoie les données reçues
    return response.json();
}