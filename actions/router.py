import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from actions.skill_manager import manager

from plugins.manager import plugin_manager

logger = logging.getLogger("NOVA.SemanticRouter")

class SemanticRouter:
    def __init__(self):
        self.reload()
        # Register for dynamic hot-reload when plugins are toggled in UI!
        plugin_manager.register_reload_listener(self.reload)

    def reload(self):
        """Re-indexes fast training phrases dynamically on the fly."""
        self.intents = manager.get_all_intents()
        
        self.tool_names = []
        self.training_sentences = []
        
        for tool, phrases in self.intents.items():
            for phrase in phrases:
                self.tool_names.append(tool)
                self.training_sentences.append(phrase)
                
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        if self.training_sentences:
            self.knowledge_base_vectors = self.vectorizer.fit_transform(self.training_sentences)
            logger.info(f"Semantic Router indexed {len(self.tool_names)} training phrases across active skills & plugins.")
        else:
            self.knowledge_base_vectors = None
            logger.warning("No skills active! Semantic Router is empty.")

    def route(self, user_text: str, threshold: float = 0.78) -> str:
        if self.knowledge_base_vectors is None or not user_text:
            return None
            
        cleaned_text = user_text.lower().strip(".!?, \t\n")

        # Instant dictation / typing match for any phrase starting with "type ..." or "write ..."
        import re
        if re.match(r'^(?:nova,?\s*)?(?:please\s*)?(?:can\s+you\s*)?(?:type\s+that|type\s+out|type|write\s+that|write\s+out|write)\s+', cleaned_text):
            logger.info("Fast Lane Router matched 'system.type_text' (Direct Dictation Prefix)")
            return "system.type_text"

        user_vector = self.vectorizer.transform([cleaned_text])
        similarities = cosine_similarity(user_vector, self.knowledge_base_vectors)[0]
        
        best_match_index = int(np.argmax(similarities))
        best_score = float(similarities[best_match_index])
        
        if best_score >= threshold:
            best_tool = self.tool_names[best_match_index]
            logger.info(f"Fast Lane Router matched '{best_tool}' (Confidence: {best_score:.2f})")
            return best_tool
        else:
            logger.info(f"Fast Lane Router rejected best match '{self.tool_names[best_match_index]}' (Confidence: {best_score:.2f} < {threshold})")
            
        return None
