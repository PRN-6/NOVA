import logging
from skills.chrome import Chrome
from skills.web_search import WebSearch
from plugins.manager import plugin_manager

logger = logging.getLogger("NOVA.SkillManager")

class SkillManager:
    def __init__(self):
        self.active_skills = [
            Chrome(),
            WebSearch(),
        ]
        logger.info(f"SkillManager initialized with {len(self.active_skills)} skills + {len(plugin_manager.get_all_plugins())} plugins.")

    def get_all_intents(self) -> dict:
        """Collects fast-lane training phrases from active skills and enabled plugins."""
        intents_dict = {}
        for skill in self.active_skills:
            intents_dict[skill.name] = skill.fast_intents
            
        # Merge plugin intents
        intents_dict.update(plugin_manager.get_active_fast_intents())
        return intents_dict

    def get_system_prompt_descriptions(self) -> str:
        """Collects descriptions for Ollama's system prompt."""
        descriptions = []
        for skill in self.active_skills:
            descriptions.append(skill.description)
            
        # Merge plugin descriptions
        plugin_descs = plugin_manager.get_active_system_descriptions()
        if plugin_descs:
            descriptions.append(plugin_descs)
            
        return "\n".join(descriptions)

    def execute_skill(self, tool_name: str, text: str) -> bool:
        """Finds the correct skill or plugin action and executes it."""
        for skill in self.active_skills:
            if skill.name == tool_name:
                return skill.execute(text)
                
        # Check plugin actions
        return plugin_manager.execute_action(tool_name, text)

# Create a global instance that executor.py and router.py will use
manager = SkillManager()
