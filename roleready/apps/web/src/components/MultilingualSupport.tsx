"use client";

import React, { useState, useEffect } from 'react';

interface LanguageInfo {
  language: string;
  language_name: string;
  supported: boolean;
}

interface TranslationResult {
  original_text: string;
  translated_text: string;
  source_language: string;
  target_language: string;
}

interface MultilingualSupportProps {
  resumeContent: string;
  onLanguageDetected?: (language: string) => void;
  onTranslationComplete?: (translation: TranslationResult) => void;
}

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

const SUPPORTED_LANGUAGES = {
  'en': 'English',
  'es': 'Spanish',
  'fr': 'French',
  'de': 'German',
  'it': 'Italian',
  'pt': 'Portuguese',
  'ru': 'Russian',
  'zh': 'Chinese',
  'ja': 'Japanese',
  'ko': 'Korean',
  'hi': 'Hindi',
  'ar': 'Arabic',
  'nl': 'Dutch',
  'sv': 'Swedish',
  'da': 'Danish',
  'no': 'Norwegian',
  'fi': 'Finnish',
  'pl': 'Polish',
  'tr': 'Turkish',
  'he': 'Hebrew'
};

export default function MultilingualSupport({ 
  resumeContent, 
  onLanguageDetected, 
  onTranslationComplete 
}: MultilingualSupportProps) {
  const [detectedLanguage, setDetectedLanguage] = useState<LanguageInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState<string>('en');
  const [translationResult, setTranslationResult] = useState<TranslationResult | null>(null);
  const [translating, setTranslating] = useState(false);

  const detectLanguage = async () => {
    if (!resumeContent || resumeContent.length < 10) {
      setError('Resume content is too short for language detection');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API}/step10/multilingual/detect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ text: resumeContent })
      });

      if (!response.ok) {
        throw new Error('Failed to detect language');
      }

      const data = await response.json();
      setDetectedLanguage(data);
      
      if (onLanguageDetected) {
        onLanguageDetected(data.language);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Language detection failed');
    } finally {
      setLoading(false);
    }
  };

  const translateText = async (targetLanguage: string) => {
    if (!resumeContent) {
      setError('No content to translate');
      return;
    }

    setTranslating(true);
    setError(null);

    try {
      const response = await fetch(`${API}/step10/multilingual/translate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          text: resumeContent,
          target_language: targetLanguage,
          source_language: detectedLanguage?.language || 'auto'
        })
      });

      if (!response.ok) {
        throw new Error('Translation failed');
      }

      const data = await response.json();
      setTranslationResult(data);
      
      if (onTranslationComplete) {
        onTranslationComplete(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Translation failed');
    } finally {
      setTranslating(false);
    }
  };

  useEffect(() => {
    if (resumeContent && resumeContent.length > 10) {
      detectLanguage();
    }
  }, [resumeContent]);

  const getLanguageFlag = (langCode: string) => {
    const flags: Record<string, string> = {
      'en': '🇺🇸',
      'es': '🇪🇸',
      'fr': '🇫🇷',
      'de': '🇩🇪',
      'it': '🇮🇹',
      'pt': '🇵🇹',
      'ru': '🇷🇺',
      'zh': '🇨🇳',
      'ja': '🇯🇵',
      'ko': '🇰🇷',
      'hi': '🇮🇳',
      'ar': '🇸🇦',
      'nl': '🇳🇱',
      'sv': '🇸🇪',
      'da': '🇩🇰',
      'no': '🇳🇴',
      'fi': '🇫🇮',
      'pl': '🇵🇱',
      'tr': '🇹🇷',
      'he': '🇮🇱'
    };
    return flags[langCode] || '🌍';
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 w-full">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">🌍</span>
        <h3 className="font-bold text-gray-900">Multilingual Support</h3>
      </div>
      
      <div className="space-y-4">
        {/* Language Detection */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Detected Language</span>
            <button 
              onClick={detectLanguage}
              disabled={loading || !resumeContent}
              className="px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 text-sm"
            >
              {loading ? 'Detecting...' : 'Detect'}
            </button>
          </div>

          {detectedLanguage && (
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <span className="text-2xl">{getLanguageFlag(detectedLanguage.language)}</span>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{detectedLanguage.language_name}</span>
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    detectedLanguage.supported 
                      ? 'bg-green-100 text-green-700' 
                      : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {detectedLanguage.supported ? '✓ Supported' : '⚠ Limited Support'}
                  </span>
                </div>
                <p className="text-xs text-gray-600">
                  Language code: {detectedLanguage.language.toUpperCase()}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Translation */}
        {detectedLanguage && detectedLanguage.language !== 'en' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Translate to English</span>
              <button 
                onClick={() => translateText('en')}
                disabled={translating}
                className="px-3 py-1 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 text-sm"
              >
                {translating ? 'Translating...' : 'Translate'}
              </button>
            </div>

            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                ⚠️ Translating your resume to English will improve AI analysis and job matching accuracy.
                Your original text will be preserved.
              </p>
            </div>
          </div>
        )}

        {/* Custom Translation */}
        <div className="space-y-3">
          <span className="text-sm font-medium">Translate to Other Language</span>
          <div className="flex gap-2">
            <select 
              value={selectedLanguage} 
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {Object.entries(SUPPORTED_LANGUAGES).map(([code, name]) => (
                <option key={code} value={code}>
                  {getLanguageFlag(code)} {name}
                </option>
              ))}
            </select>
            <button 
              onClick={() => translateText(selectedLanguage)}
              disabled={translating || selectedLanguage === detectedLanguage?.language}
              className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 text-sm"
            >
              {translating ? 'Translating...' : '🌍'}
            </button>
          </div>
        </div>

        {/* Translation Result */}
        {translationResult && (
          <div className="space-y-3">
            <span className="text-sm font-medium">Translation Result</span>
            <div className="space-y-2">
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="text-xs text-blue-600 font-medium mb-1">
                  {SUPPORTED_LANGUAGES[translationResult.target_language as keyof typeof SUPPORTED_LANGUAGES]}
                </div>
                <p className="text-sm">{translationResult.translated_text}</p>
              </div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 text-sm">⚠️ {error}</p>
          </div>
        )}

        {/* Language Support Info */}
        <div className="pt-4 border-t">
          <div className="text-xs text-gray-600 space-y-1">
            <p>✅ Full support: Resume analysis, AI suggestions, and job matching</p>
            <p>⚠️ Limited support: Basic analysis with reduced accuracy</p>
            <p>🌍 Supporting {Object.keys(SUPPORTED_LANGUAGES).length} languages globally</p>
          </div>
        </div>
      </div>
    </div>
  );
}