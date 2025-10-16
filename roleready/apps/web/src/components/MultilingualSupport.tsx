"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Globe, Languages, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';

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
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Globe className="h-5 w-5" />
          Multilingual Support
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Language Detection */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Detected Language</span>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={detectLanguage}
              disabled={loading || !resumeContent}
            >
              {loading ? (
                <RefreshCw className="h-3 w-3 animate-spin mr-1" />
              ) : (
                <Languages className="h-3 w-3 mr-1" />
              )}
              Detect
            </Button>
          </div>

          {detectedLanguage && (
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <span className="text-2xl">{getLanguageFlag(detectedLanguage.language)}</span>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{detectedLanguage.language_name}</span>
                  <Badge variant={detectedLanguage.supported ? "default" : "secondary"}>
                    {detectedLanguage.supported ? (
                      <>
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Supported
                      </>
                    ) : (
                      <>
                        <AlertCircle className="h-3 w-3 mr-1" />
                        Limited Support
                      </>
                    )}
                  </Badge>
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
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => translateText('en')}
                disabled={translating}
              >
                {translating ? (
                  <RefreshCw className="h-3 w-3 animate-spin mr-1" />
                ) : (
                  <Languages className="h-3 w-3 mr-1" />
                )}
                Translate
              </Button>
            </div>

            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Translating your resume to English will improve AI analysis and job matching accuracy.
                Your original text will be preserved.
              </AlertDescription>
            </Alert>
          </div>
        )}

        {/* Custom Translation */}
        <div className="space-y-3">
          <span className="text-sm font-medium">Translate to Other Language</span>
          <div className="flex gap-2">
            <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
              <SelectTrigger className="flex-1">
                <SelectValue placeholder="Select target language" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(SUPPORTED_LANGUAGES).map(([code, name]) => (
                  <SelectItem key={code} value={code}>
                    <div className="flex items-center gap-2">
                      <span>{getLanguageFlag(code)}</span>
                      <span>{name}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button 
              onClick={() => translateText(selectedLanguage)}
              disabled={translating || selectedLanguage === detectedLanguage?.language}
            >
              {translating ? (
                <RefreshCw className="h-3 w-3 animate-spin" />
              ) : (
                <Languages className="h-3 w-3" />
              )}
            </Button>
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
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Language Support Info */}
        <div className="pt-4 border-t">
          <div className="text-xs text-gray-600 space-y-1">
            <p>✅ Full support: Resume analysis, AI suggestions, and job matching</p>
            <p>⚠️ Limited support: Basic analysis with reduced accuracy</p>
            <p>🌍 Supporting {Object.keys(SUPPORTED_LANGUAGES).length} languages globally</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
