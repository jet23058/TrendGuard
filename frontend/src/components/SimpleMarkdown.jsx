import React from 'react';

// --- 簡易 Markdown 渲染元件 ---
const SimpleMarkdown = ({ content }) => {
    if (!content) return null;

    // 1. 處理標題 (## Title)
    // 2. 處理列表 (- Item)
    // 3. 處理粗體 (**Bold**)
    // 4. 處理換行

    const lines = content.split('\n');

    return (
        <div className="space-y-4 text-gray-300 leading-relaxed">
            {lines.map((line, index) => {
                // H2
                if (line.startsWith('## ')) {
                    return <h2 key={index} className="text-xl font-bold text-white mt-6 mb-3 border-l-4 border-blue-500 pl-3">{line.replace('## ', '')}</h2>;
                }
                // H3
                if (line.startsWith('### ')) {
                    return <h3 key={index} className="text-lg font-bold text-blue-200 mt-4 mb-2">{line.replace('### ', '')}</h3>;
                }
                // List Item
                if (line.trim().startsWith('- ')) {
                    const text = line.trim().substring(2);
                    // 處理粗體
                    const parts = text.split(/(\*\*.*?\*\*)/g);
                    return (
                        <div key={index} className="flex gap-2 ml-4">
                            <span className="text-blue-500 mt-1.5">•</span>
                            <span>
                                {parts.map((part, i) => {
                                    if (part.startsWith('**') && part.endsWith('**')) {
                                        return <strong key={i} className="text-white font-bold">{part.slice(2, -2)}</strong>;
                                    }
                                    return part;
                                })}
                            </span>
                        </div>
                    );
                }
                // Empty line
                if (line.trim() === '') {
                    return <div key={index} className="h-2"></div>;
                }

                // Normal text with bold support
                const parts = line.split(/(\*\*.*?\*\*)/g);
                return (
                    <p key={index}>
                        {parts.map((part, i) => {
                            if (part.startsWith('**') && part.endsWith('**')) {
                                return <strong key={i} className="text-white font-bold">{part.slice(2, -2)}</strong>;
                            }
                            return part;
                        })}
                    </p>
                );
            })}
        </div>
    );
};

export default SimpleMarkdown;
