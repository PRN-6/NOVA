import logging
import subprocess
import webbrowser
import ollama

logger = logging.getLogger("NOVA.ActionExecutor")

#os-level commands
def open_chrome():
    logger.info("AI Acrion: Launching Google chrome")
    subprocess.Popen("Start chrome",shell=True)

def open_youtube():
    logger.info("AI Action: Opening YouTube")
    webbrowser.open("https://www.youtube.com")

def open_vscode():
    logger.info("AI Action: Launching vscode")
    subprocess.Popen("code",shell=True)

#map fuction to string keys
Tool_map = {
    "open_chrome": open_chrome,
    "open_youtube": open_youtube,
    "open_vscode": open_vscode
}


def execute_system_command(text: str) -> bool:
    """
    Sends the user's speech to Qwen. Qwen selects the tool name, 
    and we run the corresponding Python function.
    """

    system_prompt = (
        "You are the brain of NOVA, a desktop assistant.\n"
        "You must select the most appropriate tool to run based on the user's request.\n"
        "Available tools:\n"
        "- open_chrome: Use this when the user wants to browse, search, or open Google Chrome.\n"
        "- open_youtube: Use this when the user wants to watch videos or open YouTube.\n"
        "- open_vscode: Use this when the user wants to code, write script, or open VS Code.\n\n"
        "If none of the tools match, return the word: None\n"
        "Otherwise, return ONLY the exact name of the tool. Do not include any punctuation, quotes, or extra text."
    )

    try:
        #call the local model running in ollama
        response = ollama.chat(
            model = 'qwen2.5:7b',
            messages=[
                {'role': 'system','content': system_prompt},
                {'role': 'user' , 'content': text}
            ]
        )

        selected_tool = response['message']['content'].strip()
        logger.info(f"AI Selected: '{selected_tool}' for input: '{text}'")

        #if model selected a valid function ,run this
        if selected_tool in Tool_map:
            Tool_map[selected_tool]()
            return True
        
    except Exception as e:
        logger.error(f"Error communicating with local ai{e}")

    return False