// La colonne de gauche : le logo, la liste des discussions et la déconnexion.
// Elle reçoit tout ce dont elle a besoin de la page (les "props").
export default function Sidebar({ chats, selectedChatId, onSelectChat, onNewChat, onLogout }) {
    return (
        <aside className="flex w-72 shrink-0 flex-col border-r border-gray-200 bg-white">
            {/* Le logo : un clic ramène à l'écran d'accueil (nouvelle discussion) */}
            <button
                type="button"
                onClick={onNewChat}
                className="border-b border-gray-200 px-6 py-5 text-left text-lg text-violet-600 hover:bg-gray-50"
                aria-label="NEWSFOUNDRY, démarrer une nouvelle discussion"
            >
                NEWSFOUNDRY 🤖
            </button>

            {/* La liste des discussions */}
            <nav aria-label="Mes discussions" className="flex-1 overflow-y-auto">
                {chats.length === 0 ? (
                    <p className="px-6 py-4 text-sm text-gray-500">Aucune discussion pour l&apos;instant.</p>
                ) : (
                    <ul>
                        {chats.map((chat) => {
                            const isSelected = chat.id === selectedChatId;
                            return (
                                <li key={chat.id}>
                                    <button
                                        type="button"
                                        onClick={() => onSelectChat(chat.id)}
                                        aria-current={isSelected ? "page" : undefined}
                                        className={`w-full border-b border-gray-200 px-6 py-4 text-left hover:bg-gray-50 ${isSelected ? "bg-gray-100" : ""
                                            }`}
                                    >
                                        <span className="block text-sm text-gray-900">Discussion du</span>
                                        <span className="block text-xs text-gray-500">
                                            {new Date(chat.created_at).toLocaleDateString("fr-FR")}
                                        </span>
                                    </button>
                                </li>
                            );
                        })}
                    </ul>
                )}
            </nav>

            {/* La déconnexion, en bas */}
            <button
                type="button"
                onClick={onLogout}
                className="px-6 py-5 text-left text-sm text-gray-700 hover:bg-gray-50"
            >
                ⏻ Se déconnecter
            </button>
        </aside>
    );
}