import os
import platform
import subprocess
from collections import deque
from dotenv import load_dotenv
import google.generativeai as genai
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError(Fore.RED + "❌ GEMINI_API_KEY not found in .env file")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

# Track command history
history = deque(maxlen=10)

# Dangerous commands filter
DANGEROUS_CMDS = ["del", "erase", "format", "shutdown", "rd", "rmdir"]

def is_safe(cmd: str) -> bool:
    return not any(cmd.lower().startswith(dc) for dc in DANGEROUS_CMDS)

# Generate command with structured prompting
def get_command(natural_language: str, os_type: str):
    prompt = f"""
You are a {os_type} command line expert.
Convert the following natural language request into a valid {os_type} command.

Rules:
- Return ONLY the single-line raw command.
- No quotes, no markdown, no JSON, no explanations.
- Use safe, common defaults.

Examples:
NL: Show me all running processes
Windows: tasklist
Linux/macOS: ps aux

NL: List files in current directory
Windows: dir
Linux/macOS: ls -la

NL: Check my IP address
Windows: ipconfig
Linux/macOS: ifconfig

NL Input: {natural_language}
"""
    response = model.generate_content(prompt)
    return response.text.strip("` \n")

# Optional explain mode
def explain_command(cmd: str, os_type: str):
    prompt = f"""
Explain in simple terms what this {os_type} command does:
{cmd}
"""
    response = model.generate_content(prompt)
    return response.text.strip()

# Main loop
def main():
    os_type = platform.system()
    print(Fore.CYAN + f"🔮 AI Shell – Powered by Gemini ({os_type})\n")

    while True:
        nl_input = input(Fore.YELLOW + "Enter command (or type 'exit'): " + Style.RESET_ALL).strip()
        if nl_input.lower() == "exit":
            print(Fore.MAGENTA + "👋 Exiting AI Shell.")
            break

        if nl_input.lower() == "history":
            print(Fore.CYAN + "\n📜 Command History:")
            for i, cmd in enumerate(history, 1):
                print(f"{i}. {cmd}")
            print()
            continue

        if nl_input.lower().startswith("repeat"):
            try:
                idx = int(nl_input.split(" ")[1]) - 1
                bash_cmd = history[idx]
                print(Fore.GREEN + f"\n🔁 Repeating command:\n{bash_cmd}\n")
            except:
                print(Fore.RED + "❌ Invalid history index.\n")
                continue
        else:
            bash_cmd = get_command(nl_input, os_type)

        if not bash_cmd:
            print(Fore.RED + "❌ Could not generate a command.\n")
            continue

        print(Fore.GREEN + f"\n🧠 Interpreted command:\n{bash_cmd}\n")

        # Check if user wants explanation
        if "--explain" in nl_input:
            print(Fore.CYAN + "💡 Explanation:\n" + explain_command(bash_cmd, os_type) + "\n")
            continue

        # Safety check
        if not is_safe(bash_cmd):
            print(Fore.RED + "⚠️ Command blocked for safety.\n")
            continue

        # Confirm execution
        confirm = input(Fore.YELLOW + "⚠️ Run this command? (y/n): " + Style.RESET_ALL).strip().lower()
        if confirm != "y":
            print(Fore.MAGENTA + "❎ Skipped.\n")
            continue

        try:
            result = subprocess.run(bash_cmd, shell=True, capture_output=True, text=True)
            output = result.stdout.strip()
            error = result.stderr.strip()

            if output:
                print(Fore.WHITE + f"📄 Output:\n{output}\n")
            if error:
                print(Fore.RED + f"⚠️ Error:\n{error}\n")

            history.append(bash_cmd)

        except Exception as e:
            print(Fore.RED + f"❌ Execution error: {e}\n")

if __name__ == "__main__":
    main()
