import React, { useState } from 'react';
import { GymHeader } from './components/landing/GymHeader';
import { GymHero } from './components/landing/GymHero';
import { ChatLauncher } from './components/chatbot/ChatLauncher';
import { ChatWindow } from './components/chatbot/ChatWindow';
import { DemoToolbar } from './components/chatbot/DemoToolbar';
import { ChatState } from './types/chat';

// Flag de modo demo: con cambiar a false se oculta todo el panel y los controles de prueba
const DEMO_MODE = true;

export default function App() {
  const [isChatOpen, setIsChatOpen] = useState<boolean>(true);
  const [forceMobileView, setForceMobileView] = useState<boolean>(false);
  const [currentState, setCurrentState] = useState<ChatState>('ok');

  const handleOpenChat = () => {
    setIsChatOpen(true);
  };

  const handleCloseChat = () => {
    setIsChatOpen(false);
  };

  const handleToggleMobileView = () => {
    setForceMobileView((prev) => !prev);
  };

  const handleForceState = (state: ChatState) => {
    setCurrentState(state);
    if (!isChatOpen) {
      setIsChatOpen(true);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white relative flex flex-col font-sans selection:bg-[#DC2626] selection:text-white">
      {/* Barra de navegación de Silver Gym Surco */}
      <GymHeader />

      {/* Sección Hero con fondo deportivo */}
      <GymHero onOpenChat={handleOpenChat} />

      {/* Botón flotante launcher "Pregúntale a Silver" */}
      <ChatLauncher onClick={handleOpenChat} isOpen={isChatOpen} />

      {/* Ventana de chat (escritorio flotante 400x680px o móvil pantalla completa) */}
      <ChatWindow
        isOpen={isChatOpen}
        onClose={handleCloseChat}
        forceMobileView={forceMobileView}
        forcedState={currentState}
      />

      {/* Selector Demo: alternar vista escritorio/móvil y forzar estados A-E */}
      <DemoToolbar
        demoMode={DEMO_MODE}
        forceMobileView={forceMobileView}
        onToggleMobileView={handleToggleMobileView}
        onForceState={handleForceState}
        currentState={currentState}
      />
    </div>
  );
}
