import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';

export interface Email {
  id: string;
  user_id: string;
  folder: string;
  sender: string;
  sender_email: string | null;
  subject: string;
  body: string;
  snippet: string | null;
  is_read: boolean;
  is_starred: boolean;
  received_at: string;
  created_at: string;
}

export type EmailFolder = 'inbox' | 'sent' | 'drafts' | 'trash' | 'starred';

interface UseEmailsResult {
  emails: Email[];
  currentFolder: EmailFolder;
  selectedEmail: Email | null;
  isLoading: boolean;
  error: string | null;
  unreadCount: number;
  setFolder: (folder: EmailFolder) => void;
  selectEmail: (email: Email | null) => void;
  markAsRead: (emailId: string) => Promise<void>;
  toggleStar: (emailId: string) => Promise<void>;
  deleteEmail: (emailId: string) => Promise<void>;
  searchEmails: (query: string) => void;
  refreshEmails: () => Promise<void>;
  getEmailByNumber: (num: number) => Email | null;
}

export function useEmails(): UseEmailsResult {
  const { user } = useAuth();
  const [emails, setEmails] = useState<Email[]>([]);
  const [filteredEmails, setFilteredEmails] = useState<Email[]>([]);
  const [currentFolder, setCurrentFolder] = useState<EmailFolder>('inbox');
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchEmails = useCallback(async () => {
    if (!user) {
      setEmails([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      let query = supabase
        .from('emails')
        .select('*')
        .eq('user_id', user.id)
        .order('received_at', { ascending: false });

      // Handle folder filtering
      if (currentFolder === 'starred') {
        query = query.eq('is_starred', true);
      } else {
        query = query.eq('folder', currentFolder);
      }

      const { data, error: fetchError } = await query;

      if (fetchError) throw fetchError;

      setEmails(data || []);
      setFilteredEmails(data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch emails');
    } finally {
      setIsLoading(false);
    }
  }, [user, currentFolder]);

  // Seed demo emails for new users
  const seedDemoEmails = useCallback(async () => {
    if (!user) return;

    const { data: existingEmails } = await supabase
      .from('emails')
      .select('id')
      .eq('user_id', user.id)
      .limit(1);

    if (existingEmails && existingEmails.length > 0) return;

    const demoEmails = [
      {
        user_id: user.id,
        folder: 'inbox',
        sender: 'Sarah Johnson',
        sender_email: 'sarah.johnson@company.com',
        subject: 'Quarterly Report Review',
        body: 'Hi,\n\nI wanted to follow up on the quarterly report we discussed last week. The sales figures look promising, with a 15% increase compared to last quarter.\n\nCould you please review the attached document and let me know your thoughts by Friday?\n\nBest regards,\nSarah',
        snippet: 'I wanted to follow up on the quarterly report...',
        is_read: false,
        is_starred: true,
        received_at: new Date(Date.now() - 3600000).toISOString(),
      },
      {
        user_id: user.id,
        folder: 'inbox',
        sender: 'Tech Support',
        sender_email: 'support@techhelp.com',
        subject: 'Your Support Ticket #12345 Has Been Resolved',
        body: 'Hello,\n\nWe are pleased to inform you that your support ticket regarding the login issue has been resolved.\n\nIf you experience any further issues, please don\'t hesitate to contact us.\n\nThank you for your patience.\n\nTech Support Team',
        snippet: 'Your support ticket regarding the login issue has been resolved...',
        is_read: false,
        is_starred: false,
        received_at: new Date(Date.now() - 7200000).toISOString(),
      },
      {
        user_id: user.id,
        folder: 'inbox',
        sender: 'Marketing Team',
        sender_email: 'marketing@newsletter.com',
        subject: 'New Product Launch - Early Access Invitation',
        body: 'Dear Valued Customer,\n\nWe are excited to announce the launch of our newest product line! As a loyal customer, you have been selected for early access.\n\nClick the link below to explore our new collection before anyone else.\n\nThank you for your continued support!\n\nThe Marketing Team',
        snippet: 'We are excited to announce the launch of our newest product...',
        is_read: true,
        is_starred: false,
        received_at: new Date(Date.now() - 86400000).toISOString(),
      },
      {
        user_id: user.id,
        folder: 'inbox',
        sender: 'Michael Chen',
        sender_email: 'mchen@partner.org',
        subject: 'Meeting Reschedule Request',
        body: 'Hi there,\n\nI hope this email finds you well. I need to reschedule our meeting originally planned for tomorrow at 2 PM.\n\nWould Thursday at 10 AM work for you instead?\n\nPlease let me know at your earliest convenience.\n\nBest,\nMichael',
        snippet: 'I need to reschedule our meeting originally planned for tomorrow...',
        is_read: false,
        is_starred: false,
        received_at: new Date(Date.now() - 172800000).toISOString(),
      },
      {
        user_id: user.id,
        folder: 'sent',
        sender: 'Me',
        sender_email: user.email || '',
        subject: 'Re: Project Update',
        body: 'Hi Team,\n\nThank you for the update. The progress looks great!\n\nI have reviewed the documents and everything looks good to proceed to the next phase.\n\nLet me know if you need any additional resources.\n\nBest regards',
        snippet: 'Thank you for the update. The progress looks great...',
        is_read: true,
        is_starred: false,
        received_at: new Date(Date.now() - 259200000).toISOString(),
      },
    ];

    await supabase.from('emails').insert(demoEmails);
  }, [user]);

  useEffect(() => {
    if (user) {
      seedDemoEmails().then(() => fetchEmails());
    }
  }, [user, fetchEmails, seedDemoEmails]);

  useEffect(() => {
    fetchEmails();
  }, [currentFolder, fetchEmails]);

  // Filter emails based on search
  useEffect(() => {
    if (!searchQuery) {
      setFilteredEmails(emails);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = emails.filter(email =>
      email.subject.toLowerCase().includes(query) ||
      email.sender.toLowerCase().includes(query) ||
      email.body.toLowerCase().includes(query)
    );
    setFilteredEmails(filtered);
  }, [searchQuery, emails]);

  const unreadCount = emails.filter(e => !e.is_read).length;

  const setFolder = useCallback((folder: EmailFolder) => {
    setCurrentFolder(folder);
    setSelectedEmail(null);
    setSearchQuery('');
  }, []);

  const selectEmail = useCallback((email: Email | null) => {
    setSelectedEmail(email);
    if (email && !email.is_read) {
      // Mark as read when selected
      supabase
        .from('emails')
        .update({ is_read: true })
        .eq('id', email.id)
        .then(() => {
          setEmails(prev => prev.map(e => 
            e.id === email.id ? { ...e, is_read: true } : e
          ));
        });
    }
  }, []);

  const markAsRead = async (emailId: string) => {
    await supabase.from('emails').update({ is_read: true }).eq('id', emailId);
    setEmails(prev => prev.map(e => e.id === emailId ? { ...e, is_read: true } : e));
  };

  const toggleStar = async (emailId: string) => {
    const email = emails.find(e => e.id === emailId);
    if (!email) return;

    await supabase.from('emails').update({ is_starred: !email.is_starred }).eq('id', emailId);
    setEmails(prev => prev.map(e => 
      e.id === emailId ? { ...e, is_starred: !e.is_starred } : e
    ));
  };

  const deleteEmail = async (emailId: string) => {
    const email = emails.find(e => e.id === emailId);
    if (!email) return;

    if (email.folder === 'trash') {
      // Permanently delete
      await supabase.from('emails').delete().eq('id', emailId);
    } else {
      // Move to trash
      await supabase.from('emails').update({ folder: 'trash' }).eq('id', emailId);
    }

    setEmails(prev => prev.filter(e => e.id !== emailId));
    if (selectedEmail?.id === emailId) {
      setSelectedEmail(null);
    }
  };

  const searchEmails = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  const refreshEmails = useCallback(async () => {
    await fetchEmails();
  }, [fetchEmails]);

  const getEmailByNumber = useCallback((num: number): Email | null => {
    return filteredEmails[num - 1] || null;
  }, [filteredEmails]);

  return {
    emails: filteredEmails,
    currentFolder,
    selectedEmail,
    isLoading,
    error,
    unreadCount,
    setFolder,
    selectEmail,
    markAsRead,
    toggleStar,
    deleteEmail,
    searchEmails,
    refreshEmails,
    getEmailByNumber,
  };
}
