import logging
import ollama
from actions.skill_manager import manager
from actions.router import SemanticRouter

logger = logging.getLogger("NOVA.ActionExecutor")
fast_router = SemanticRouter()

def preload_ai_model():
    logger.info("preloading ai model")
    try:
        ollama.chat(
            model='qwen2.5:1.5b',
            messages=[{'role': 'user', 'content': 'ping'}],
            keep_alive=300
        )
        logger.info("ai model preloaded successfully")
    except Exception as e:
        logger.warning(f"could not preload ai model: {e}")

def execute_system_command(text: str) -> bool:
    """
    Sends the user's speech to Qwen. Qwen selects the tool name, 
    and we run the corresponding Python function.
    """
    # 1. Fast Lane (Instant Execution)
    fast_tool = fast_router.route(text)
    if fast_tool:
        return manager.execute_skill(fast_tool, text)

    # 2. Slow AI Lane (Fallback)
    logger.info(f"Command '{text}' is complex. Sending to Ollama AI...")
    
    # Dynamically generate the system prompt based on active skills!
    available_tools = manager.get_system_prompt_descriptions()
    
    system_prompt = (
        "You are the brain of NOVA, a desktop assistant.\n"
        "You must select the most appropriate tool to run based on the user's request.\n"
        "Available tools:\n"
        f"{available_tools}\n\n"
        "If none of the tools match, return the word: None\n"
        "Otherwise, return ONLY the exact name of the tool. Do not include any punctuation, quotes, or extra text."
    )

    try:
        response = ollama.chat(
            model='qwen2.5:1.5b',
            keep_alive=300,
            options={
                'temperature': 0.2,
                'top_p': 0.9,
                'top_k': 40
            },
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': text}
            ]
        )

        selected_tool = response['message']['content'].strip()
        logger.info(f"AI Selected: '{selected_tool}' for input: '{text}'")

        if selected_tool != "None":
            return manager.execute_skill(selected_tool, text)
        
    except Exception as e:
        logger.error(f"Error communicating with local ai: {e}")

    return False