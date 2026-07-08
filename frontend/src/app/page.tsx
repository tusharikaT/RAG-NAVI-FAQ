'use client';

import React, { useState, useRef, useEffect } from 'react';

type Message = {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  citation?: string | null;
  footer?: string | null;
  disclaimer?: string | null;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
      if (e.target.value.trim() === '') {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleSend = async (text: string) => {
    const trimmedText = text.trim();
    if (!trimmedText || isLoading) return;

    // Reset input
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';

    const userMessage: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text: trimmedText,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${apiUrl}/api/v1/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: trimmedText }),
      });
      const data = await response.json();

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: data.answer || "Sorry, I couldn't process that request.",
        citation: data.citation,
        footer: data.footer,
        disclaimer: data.disclaimer,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error(error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: 'Connection error. Please ensure the backend service is running at 127.0.0.1:8000.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(input);
    }
  };

  return (
    <>
      {/* SideNavBar */}
      <aside className="bg-surface-container-low/60 dark:bg-surface-container-low/60 backdrop-blur-lg h-screen w-64 fixed left-0 top-0 border-r border-white/10 shadow-none flex flex-col p-md z-50">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8 px-2">
          <div className="w-10 h-10 rounded-full bg-primary-container/20 flex items-center justify-center shrink-0">
            <span className="material-symbols-outlined text-primary">account_circle</span>
          </div>
          <div>
            <h2 className="text-headline-md font-headline-md font-black text-primary leading-tight text-lg">Navi MF Assistant</h2>
          </div>
        </div>
        {/* CTA */}
        <button className="w-full bg-primary text-on-primary py-3 px-4 rounded-xl hover:bg-primary-fixed transition-colors flex items-center justify-center gap-2 mb-8 text-label-md font-label-md font-semibold">
          <span className="material-symbols-outlined text-[20px]">add</span>
          New Chat
        </button>
        {/* Tabs */}
        <nav className="flex flex-col gap-2">
          <a className="flex items-center gap-3 px-4 py-3 rounded-lg bg-primary/20 text-primary border-r-2 border-primary transition-all duration-200 ease-in-out text-label-md font-label-md" href="#">
            <span className="material-symbols-outlined">chat</span>
            Chat
          </a>
          <a className="flex items-center gap-3 px-4 py-3 rounded-lg text-on-surface-variant/70 hover:text-on-surface hover:bg-white/5 transition-all duration-200 ease-in-out text-label-md font-label-md" href="#">
            <span className="material-symbols-outlined">history</span>
            History
          </a>
        </nav>
      </aside>

      {/* TopAppBar */}
      <header className="bg-surface/60 dark:bg-surface/60 backdrop-blur-md fixed top-0 w-[calc(100%-256px)] z-40 border-b border-white/10 shadow-none flex justify-between items-center px-gutter py-md max-w-screen-xl mx-auto right-0 left-64">
        <div className="flex flex-col">
          <span className="text-code-sm font-code-sm text-on-surface-variant flex items-center gap-1 mt-1">
            ⚠️ Facts-only. No investment advice.
          </span>
        </div>
        <div className="flex gap-4 items-center">
        </div>
      </header>

      {/* Main Chat Canvas */}
      <main className="flex-1 flex flex-col pt-[90px] pb-[100px] max-w-[800px] mx-auto w-full relative h-full">
        {/* Background Ambient Glow */}
        <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-container/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary-container/10 rounded-full blur-3xl"></div>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto px-4 z-10 scroll-smooth flex flex-col gap-6 pt-8 pb-4">
          
          {messages.length === 0 && !isLoading && (
            <div className="flex flex-col items-center justify-center h-full text-center message-enter">
              <div className="w-16 h-16 rounded-2xl glass-panel flex items-center justify-center mb-6 text-primary shadow-[0_0_30px_rgba(192,193,255,0.2)]">
                <span className="material-symbols-outlined text-4xl">smart_toy</span>
              </div>
              <h2 className="text-display-lg-mobile font-display-lg-mobile text-on-surface mb-4">How can I help you today?</h2>
              <p className="text-body-md font-body-md text-on-surface-variant mb-8 max-w-md">
                Ask me anything about Navi Mutual Funds. I can provide facts, figures, and technical details.
              </p>
              <div className="flex flex-col gap-3 w-full max-w-lg">
                {[
                  "What is the expense ratio of Navi Nifty 50?",
                  "What is the exit load for Navi ELSS?",
                  "What is the minimum SIP amount for Navi Liquid Fund?",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => handleSend(suggestion)}
                    className="suggestion-btn glass-panel text-left px-6 py-4 rounded-xl hover:bg-white/5 transition-colors border border-white/10 hover:border-primary/50 text-body-md font-body-md flex items-center justify-between group"
                  >
                    {suggestion}
                    <span className="material-symbols-outlined text-on-surface-variant group-hover:text-primary transition-colors">arrow_forward</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} w-full message-enter`}>
              {msg.sender === 'user' ? (
                <div className="max-w-[85%] bg-primary text-on-primary px-6 py-3 rounded-2xl rounded-tr-sm shadow-md">
                  <p className="text-body-md font-body-md whitespace-pre-wrap">{msg.text}</p>
                </div>
              ) : (
                <div className="flex gap-4 max-w-[90%]">
                  <div className="w-8 h-8 rounded-full bg-surface-variant border border-white/10 flex items-center justify-center shrink-0 mt-1">
                    <span className="material-symbols-outlined text-primary text-sm">smart_toy</span>
                  </div>
                  <div className="bot-bubble text-on-surface px-6 py-4 rounded-2xl rounded-tl-sm shadow-md flex flex-col gap-3">
                    <p className={`text-body-md font-body-md whitespace-pre-wrap leading-relaxed ${msg.text.includes('error') ? 'text-error' : 'text-on-surface-variant'}`}>
                      {msg.text}
                    </p>
                    
                    {(msg.citation || msg.footer || msg.disclaimer) && !msg.text.includes('error') && (
                      <div className="flex flex-col gap-2 mt-2 pt-3 border-t border-white/5">
                        {msg.citation && (
                          <a
                            href={msg.citation.startsWith('http') ? msg.citation : '#'}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 w-fit px-3 py-1.5 rounded-md bg-white/5 hover:bg-white/10 border border-white/10 text-label-md font-label-md text-secondary transition-colors"
                          >
                            <span className="material-symbols-outlined text-[16px]">link</span>
                            <span>{msg.citation}</span>
                          </a>
                        )}
                        <div className="flex items-center justify-between mt-1 gap-8">
                          {msg.footer && <span className="text-code-sm font-code-sm text-on-surface-variant/60">{msg.footer}</span>}
                          {msg.disclaimer && <span className="text-code-sm font-code-sm text-error/80">{msg.disclaimer}</span>}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start w-full message-enter">
              <div className="flex gap-4 max-w-[90%] items-center">
                <div className="w-8 h-8 rounded-full bg-surface-variant border border-white/10 flex items-center justify-center shrink-0">
                  <span className="material-symbols-outlined text-primary text-sm">smart_toy</span>
                </div>
                <div className="bot-bubble px-6 py-4 rounded-2xl rounded-tl-sm h-[52px] flex items-center justify-center min-w-[80px]">
                  <div className="dot-flashing"></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={chatEndRef} />
        </div>

        {/* Sticky Input Area */}
        <div className="absolute bottom-0 w-full px-4 pb-6 pt-4 bg-gradient-to-t from-background via-background to-transparent z-20">
          <div className="relative glass-panel rounded-2xl max-w-[800px] mx-auto shadow-lg shadow-black/20 focus-within:shadow-[0_0_15px_rgba(192,193,255,0.15)] transition-shadow">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              className="w-full bg-transparent border-0 text-on-surface placeholder:text-on-surface-variant/50 focus:ring-0 resize-none py-4 pl-6 pr-16 rounded-2xl max-h-32 text-body-md font-body-md focus:outline-none"
              placeholder="Ask about Navi Mutual Funds..."
              rows={1}
              disabled={isLoading}
            />
            <button
              onClick={() => handleSend(input)}
              disabled={!input.trim() || isLoading}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-primary text-on-primary rounded-xl hover:bg-primary-fixed transition-colors flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="material-symbols-outlined">send</span>
            </button>
          </div>
          <div className="text-center mt-2">
            <span className="text-code-sm font-code-sm text-on-surface-variant/50">AI generated responses. Verify before investing.</span>
          </div>
        </div>
      </main>
    </>
  );
}
