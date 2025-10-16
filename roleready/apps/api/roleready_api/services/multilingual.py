"""
Multilingual support service for RoleReady
Handles language detection, translation, and multilingual embeddings
"""

from typing import Dict, List, Optional, Tuple
import logging
from langdetect import detect, DetectorFactory, LangDetectException
from sentence_transformers import SentenceTransformer
import openai
from roleready_api.core.config import settings

# Set seed for consistent language detection
DetectorFactory.seed = 42

logger = logging.getLogger(__name__)

class MultilingualService:
    def __init__(self):
        self.supported_languages = {
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
        }
        
        # Multilingual embedding model
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # Translation mappings for common resume terms
        self.translation_mappings = {
            'en': {
                'summary': 'Summary',
                'experience': 'Experience', 
                'education': 'Education',
                'skills': 'Skills',
                'projects': 'Projects',
                'certifications': 'Certifications',
                'achievements': 'Achievements',
                'languages': 'Languages'
            },
            'es': {
                'summary': 'Resumen',
                'experience': 'Experiencia',
                'education': 'Educación', 
                'skills': 'Habilidades',
                'projects': 'Proyectos',
                'certifications': 'Certificaciones',
                'achievements': 'Logros',
                'languages': 'Idiomas'
            },
            'fr': {
                'summary': 'Résumé',
                'experience': 'Expérience',
                'education': 'Formation',
                'skills': 'Compétences', 
                'projects': 'Projets',
                'certifications': 'Certifications',
                'achievements': 'Réalisations',
                'languages': 'Langues'
            },
            'de': {
                'summary': 'Zusammenfassung',
                'experience': 'Berufserfahrung',
                'education': 'Bildung',
                'skills': 'Fähigkeiten',
                'projects': 'Projekte', 
                'certifications': 'Zertifizierungen',
                'achievements': 'Erfolge',
                'languages': 'Sprachen'
            },
            'zh': {
                'summary': '个人简介',
                'experience': '工作经验',
                'education': '教育背景',
                'skills': '技能',
                'projects': '项目经验',
                'certifications': '证书',
                'achievements': '成就',
                'languages': '语言能力'
            },
            'ja': {
                'summary': '要約',
                'experience': '経験',
                'education': '学歴',
                'skills': 'スキル',
                'projects': 'プロジェクト',
                'certifications': '資格',
                'achievements': '実績',
                'languages': '言語'
            },
            'hi': {
                'summary': 'सारांश',
                'experience': 'अनुभव',
                'education': 'शिक्षा',
                'skills': 'कौशल',
                'projects': 'परियोजनाएं',
                'certifications': 'प्रमाणपत्र',
                'achievements': 'उपलब्धियां',
                'languages': 'भाषाएं'
            }
        }

    def detect_language(self, text: str) -> str:
        """
        Detect the language of the given text
        Returns ISO 639-1 language code
        """
        try:
            if not text or len(text.strip()) < 10:
                return 'en'  # Default to English for very short text
            
            # Clean text for better detection
            clean_text = ' '.join(text.split()[:500])  # Use first 500 words
            
            detected = detect(clean_text)
            
            # Validate detected language is supported
            if detected in self.supported_languages:
                return detected
            else:
                logger.warning(f"Detected unsupported language: {detected}, defaulting to English")
                return 'en'
                
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {e}, defaulting to English")
            return 'en'
        except Exception as e:
            logger.error(f"Unexpected error in language detection: {e}")
            return 'en'

    def translate_text(self, text: str, target_lang: str = 'en', source_lang: str = 'auto') -> str:
        """
        Translate text using OpenAI API
        """
        try:
            if not text or target_lang == source_lang:
                return text
                
            # Use OpenAI for translation
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Determine source language for better translation
            if source_lang == 'auto':
                source_lang = self.detect_language(text)
            
            system_prompt = f"""You are a professional translator specializing in resume and professional document translation. 
            Translate the following text from {self.supported_languages.get(source_lang, source_lang)} to {self.supported_languages.get(target_lang, target_lang)}.
            Maintain the professional tone and format. Preserve technical terms and proper nouns when appropriate.
            Return only the translated text without any explanations or formatting."""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text  # Return original text if translation fails

    def get_multilingual_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using multilingual model
        """
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []

    def translate_resume_sections(self, sections: Dict, target_lang: str) -> Dict:
        """
        Translate resume section headings based on target language
        """
        if target_lang not in self.translation_mappings:
            return sections
            
        translations = self.translation_mappings[target_lang]
        translated_sections = {}
        
        # Translate section keys
        for key, value in sections.items():
            translated_key = translations.get(key, key)
            translated_sections[translated_key] = value
            
        return translated_sections

    def get_language_name(self, lang_code: str) -> str:
        """
        Get human-readable language name from ISO code
        """
        return self.supported_languages.get(lang_code, 'Unknown')

    def is_supported_language(self, lang_code: str) -> bool:
        """
        Check if language is supported
        """
        return lang_code in self.supported_languages

# Global instance
multilingual_service = MultilingualService()