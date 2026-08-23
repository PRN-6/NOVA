import logging
from skills.whatsapp import Whatsapp
from skills.chrome import Chrome

logger = logging.getLogger("NOVA.SkillManager")

class SkillManager:
    def __init__(self):
        self.active_skills = [
            Whatsapp(),
            Chrome(),
        ]
        logger.info(f"SkillManager loaded {len(self.active_skills)} active skills.")

    def get_all_intents(self) -> dict:
        """Collects fast-lane training phrases from all active skills."""
        intents_dict = {}
        for skill in self.active_skills:
            intents_dict[skill.name] = skill.fast_intents
        return intents_dict

    def get_system_prompt_descriptions(self) -> str:
        """Collects descriptions for Ollama's system prompt."""
        descriptions = []
        for skill in self.active_skills:
            descriptions.append(skill.description)
        return "\n".join(descriptions)

    def execute_skill(self, tool_name: str, text: str) -> bool:
        """Finds the correct skill by name and executes it."""
        for skill in self.active_skills:
            if skill.name == tool_name:
                return skill.execute(text)
        return False

# Create a global instance that executor.py and router.py will use
manager = SkillManager()
