import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from actions.skill_manager import manager

logger = logging.getLogger("NOVA.SemanticRouter")

class SemanticRouter:
    def __init__(self):
        # Dynamically load training data from the Skill Manager!
        self.intents = manager.get_all_intents()
        
        self.tool_names = []
        self.training_sentences = []
        
        for tool, phrases in self.intents.items():
            for phrase in phrases:
                self.tool_names.append(tool)
                self.training_sentences.append(phrase)
                
        self.vectorizer = TfidfVectorizer()
        if self.training_sentences:
            self.knowledge_base_vectors = self.vectorizer.fit_transform(self.training_sentences)
            logger.info(f"Semantic Router initialized with {len(self.tool_names)} training phrases.")
        else:
            self.knowledge_base_vectors = None
            logger.warning("No skills active! Semantic Router is empty.")

    def route(self, user_text: str, threshold: float = 0.5) -> str:
        if self.knowledge_base_vectors is None:
            return None
            
        user_vector = self.vectorizer.transform([user_text])
        similarities = cosine_similarity(user_vector, self.knowledge_base_vectors)[0]
        
        best_match_index = int(np.argmax(similarities))
        best_score = float(similarities[best_match_index])
        
        if best_score >= threshold:
            best_tool = self.tool_names[best_match_index]
            logger.info(f"Fast Lane Router matched '{best_tool}' (Confidence: {best_score:.2f})")
            return best_tool
            
        return None
