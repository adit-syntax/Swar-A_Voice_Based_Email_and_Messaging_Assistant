import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useEmails, EmailFolder } from '@/hooks/useEmails';
import { useVoiceCommands, VoiceCommand } from '@/hooks/useVoiceCommands';
import { FolderSidebar } from '@/components/FolderSidebar';
import { EmailList } from '@/components/EmailList';
import { EmailViewer } from '@/components/EmailViewer';
import { AssistantChat, ChatMessage } from '@/components/AssistantChat';
import { VoiceIndicator } from '@/components/VoiceIndicator';
import { VoiceOnboarding } from '@/components/VoiceOnboarding';
import { Button } from '@/components/ui/button';
import { LogOut } from 'lucide-react';

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, profile, signOut, isLoading: authLoading } = useAuth();
  const { emails, currentFolder, selectedEmail, unreadCount, isLoading: emailsLoading, setFolder, selectEmail, toggleStar, deleteEmail, getEmailByNumber } = useEmails();
  
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [onboardingComplete, setOnboardingComplete] = useState(false);

  const addMessage = useCallback((role: 'user' | 'assistant' | 'system', content: string) => {
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role,
      content,
      timestamp: new Date(),
    }]);
  }, []);

  const commands: VoiceCommand[] = [
    { patterns: ['open inbox', 'go to inbox', 'show inbox'], action: () => { setFolder('inbox'); addMessage('assistant', 'Opening inbox.'); }, description: 'Open inbox' },
    { patterns: ['open sent', 'sent mail', 'show sent'], action: () => { setFolder('sent'); addMessage('assistant', 'Opening sent folder.'); }, description: 'Open sent' },
    { patterns: ['open drafts', 'show drafts'], action: () => { setFolder('drafts'); addMessage('assistant', 'Opening drafts.'); }, description: 'Open drafts' },
    { patterns: ['open starred', 'show starred'], action: () => { setFolder('starred'); addMessage('assistant', 'Opening starred emails.'); }, description: 'Open starred' },
    { patterns: ['open trash', 'show trash'], action: () => { setFolder('trash'); addMessage('assistant', 'Opening trash.'); }, description: 'Open trash' },
    { patterns: ['read email (\\d+)', 'open email (\\d+)', 'email (\\d+)'], action: (_, params) => {
      const num = parseInt(params?.[0] || '1');
      const email = getEmailByNumber(num);
      if (email) {
        selectEmail(email);
        addMessage('assistant', `Opening email ${num} from ${email.sender}. Subject: ${email.subject}`);
      } else {
        addMessage('assistant', `Email ${num} not found.`);
      }
    }, description: 'Read email by number' },
    { patterns: ['logout', 'log out', 'sign out'], action: () => { signOut(); navigate('/auth'); }, description: 'Logout' },
    { patterns: ['help', 'what can you do', 'commands'], action: () => {
      addMessage('assistant', 'Available commands: "open inbox", "read email 1", "logout", "help". Say a folder name or email number to navigate.');
    }, description: 'Show help' },
  ];

  const { isListening, isSpeaking, isSupported, speak, startListening } = useVoiceCommands({
    commands,
    onUnrecognized: (transcript) => {
      setCurrentTranscript('');
      addMessage('user', transcript);
      addMessage('assistant', "I didn't understand that. Say 'help' for commands.");
    },
  });

  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/auth');
    }
  }, [user, authLoading, navigate]);

  useEffect(() => {
    if (onboardingComplete && isSupported) {
      startListening();
      addMessage('system', 'Voice assistant activated. Say "help" for available commands.');
    }
  }, [onboardingComplete, isSupported, startListening, addMessage]);

  if (authLoading) {
    return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full" /></div>;
  }

  if (!onboardingComplete) {
    return <VoiceOnboarding onComplete={() => setOnboardingComplete(true)} isSupported={isSupported} />;
  }

  return (
    <div className="h-screen flex bg-background">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r">
        <FolderSidebar currentFolder={currentFolder} unreadCount={unreadCount} onFolderChange={setFolder} />
      </aside>

      {/* Main Content - 3 Column Layout */}
      <div className="flex-1 flex">
        {/* Email List */}
        <div className="w-80 border-r bg-card">
          <div className="p-4 border-b flex items-center justify-between">
            <h2 className="font-semibold capitalize">{currentFolder}</h2>
            <span className="text-sm text-muted-foreground">{emails.length} emails</span>
          </div>
          <div className="h-[calc(100vh-65px)]">
            <EmailList emails={emails} selectedEmail={selectedEmail} onSelectEmail={selectEmail} onToggleStar={toggleStar} isLoading={emailsLoading} />
          </div>
        </div>

        {/* Email Viewer */}
        <div className="flex-1 bg-background">
          <EmailViewer email={selectedEmail} onToggleStar={toggleStar} onDelete={deleteEmail} onReply={() => addMessage('assistant', 'Reply feature coming soon!')} />
        </div>

        {/* Assistant Chat */}
        <div className="w-80 border-l p-4">
          <AssistantChat messages={messages} isListening={isListening} isSpeaking={isSpeaking} currentTranscript={currentTranscript} />
        </div>
      </div>

      {/* Voice Indicator */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
        <VoiceIndicator isListening={isListening} isSpeaking={isSpeaking} />
      </div>

      {/* Logout Button */}
      <Button variant="ghost" size="icon" className="fixed top-4 right-4" onClick={() => { signOut(); navigate('/auth'); }}>
        <LogOut className="w-5 h-5" />
      </Button>
    </div>
  );
}
