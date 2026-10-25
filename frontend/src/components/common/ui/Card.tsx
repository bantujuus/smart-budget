import React from 'react';

interface CardProps {
    children: React.ReactNode;
    className?: string;
    title?: string;
}

export const Card: React.FC<CardProps> = ({ children, className = '', title }) => {
    return (
        <div className={`bg-slate-900/80 backdrop-blur-md border border-slate-800/80 rounded-xl p-5 shadow-lg shadow-cyan-950/20 transition-all hover:border-slate-700 ${className}`}>
            {title && (
                <h3 className="text-sm font-semibold tracking-wider text-slate-400 uppercase mb-4">
                    {title}
                </h3>
            )}
            {children}
        </div>
    );
};