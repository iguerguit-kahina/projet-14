"use client"; // Cette page tourne dans le navigateur (formulaire, clics, local storage)

import { useState } from "react"; // pour garder en mémoire ce que tape l'utilisateur
import { useRouter } from "next/navigation"; // pour changer de page après la connexion

// L'adresse du backend, lue dans le fichier .env.local
const API_URL = process.env.NEXT_PUBLIC_API_URL;

export default function LoginPage() {
    const router = useRouter();

    // Les "états" de la page : ce qu'elle garde en mémoire
    const [email, setEmail] = useState(""); // l'email tapé
    const [password, setPassword] = useState(""); // le mot de passe tapé
    const [error, setError] = useState(""); // le message d'erreur à afficher
    const [isLoading, setIsLoading] = useState(false); // vrai pendant l'envoi au backend

    // Ce qui se passe quand on clique sur "Se connecter"
    async function handleSubmit(event) {
        event.preventDefault(); // empêche la page de se recharger
        setError(""); // on efface l'ancienne erreur
        setIsLoading(true); // on indique que l'envoi commence

        try {
            // 1. On envoie l'email et le mot de passe à la route /login du backend
            const response = await fetch(`${API_URL}/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            // 2. Mauvais email ou mot de passe → message clair pour l'utilisateur
            if (response.status === 401) {
                setError("Email ou mot de passe incorrect.");
                return;
            }

            // 3. Autre problème côté backend
            if (!response.ok) {
                setError("Une erreur est survenue. Réessayez plus tard.");
                return;
            }

            // 4. Tout est bon : on enregistre le badge dans le local storage
            const data = await response.json();
            localStorage.setItem("token", data.access_token);

            // 5. On envoie l'utilisateur vers la page d'accueil
            router.push("/");
        } catch {
            // Le backend ne répond pas du tout (arrêté, pas de connexion...)
            setError("Impossible de contacter le serveur. Vérifiez votre connexion.");
        } finally {
            setIsLoading(false); // l'envoi est terminé (réussi ou non)
        }
    }

    return (
        // Fond sombre avec une grille, comme sur la maquette
        <main className="flex min-h-screen items-center justify-center bg-[#2a2a2e] bg-[linear-gradient(to_right,#3a3a40_1px,transparent_1px),linear-gradient(to_bottom,#3a3a40_1px,transparent_1px)] bg-[size:48px_48px] p-4">
            {/* La carte blanche au centre */}
            <section className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-lg">
                {/* Le logo NEWSFOUNDRY en violet */}
                <h1 className="text-center text-2xl text-violet-600">NEWSFOUNDRY</h1>
                <p className="mt-2 text-center text-sm text-gray-500">
                    Connectez-vous pour accéder à votre assistant d&apos;actualités IA
                </p>

                {/* Le formulaire */}
                <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
                    {/* Champ email : le label est relié au champ (accessibilité) */}
                    <div className="flex flex-col gap-2">
                        <label htmlFor="email" className="text-sm text-gray-800">
                            Adresse email
                        </label>
                        <input
                            id="email"
                            type="email"
                            autoComplete="email"
                            required
                            placeholder="votre.email@exemple.com"
                            value={email}
                            onChange={(event) => setEmail(event.target.value)}
                            className="rounded-md bg-gray-100 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-violet-600"
                        />
                    </div>

                    {/* Champ mot de passe (ajouté : absent de la maquette, mais demandé par l'énoncé) */}
                    <div className="flex flex-col gap-2">
                        <label htmlFor="password" className="text-sm text-gray-800">
                            Mot de passe
                        </label>
                        <input
                            id="password"
                            type="password"
                            autoComplete="current-password"
                            required
                            placeholder="Votre mot de passe"
                            value={password}
                            onChange={(event) => setPassword(event.target.value)}
                            className="rounded-md bg-gray-100 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-violet-600"
                        />
                    </div>

                    {/* Message d'erreur : role="alert" le fait lire par les lecteurs d'écran */}
                    {error && (
                        <p role="alert" className="text-sm text-red-600">
                            {error}
                        </p>
                    )}

                    {/* Bouton noir : désactivé pendant l'envoi pour éviter les doubles clics */}
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="rounded-md bg-neutral-900 py-2 text-sm text-white hover:bg-neutral-700 disabled:bg-gray-400"
                    >
                        {isLoading ? "Connexion..." : "Se connecter"}
                    </button>
                </form>
            </section>
        </main>
    );
}