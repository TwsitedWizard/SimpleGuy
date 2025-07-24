import subprocess
import os
import sys # Import the sys module
import google.generativeai as genai

# --- Configuration ---
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    # In hook mode, we can't prompt the user, so we just exit.
    # The error will be visible if the commit fails.
    exit(1)

# --- Main Logic ---

def get_staged_diff():
    """Fetches the staged changes from Git as a diff."""
    command = ["git", "diff", "--staged"]
    # We use utf-8 to prevent errors on different systems
    result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
    return result.stdout

def generate_commit_message(diff, hook_mode=False):
    """Generates a commit message using the Gemini API."""
    if not diff:
        return "Could not generate commit message because there was no diff."

    prompt = f"""
    As an expert programmer, analyze the following code changes from 'git diff --staged' and generate a concise and informative commit message.

    **Guidelines:**
    1.  Follow the **Conventional Commits specification**.
    2.  The format MUST be: `<type>[optional scope]: <description>`
    3.  `<type>` must be one of: **feat, fix, docs, style, refactor, perf, test, chore**.
    4.  The `<description>` should be a short summary (max 50 chars) in the imperative mood (e.g., 'Add feature' not 'Added feature').
    5.  Do NOT include a message body or any extra text, just the single commit headline.

    **Code Diff:**
    ```diff
    {diff}
    ```

    **Commit Message:**
    """
    
    if not hook_mode:
        print("🤖 Calling the Git Commit Genie... (please wait)")

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        # In hook mode, we don't want a friendly message, just the error
        if hook_mode:
            return f"Error: {e}"
        return f"🚨 Error generating commit message: {e}"

# --- Execution ---

if __name__ == "__main__":
    # Check if '--hook' is passed as an argument
    is_hook_mode = "--hook" in sys.argv

    staged_diff = get_staged_diff()

    if staged_diff:
        commit_message = generate_commit_message(staged_diff, hook_mode=is_hook_mode)
        
        # In hook mode, just print the message and exit
        if is_hook_mode:
            print(commit_message)
            exit(0)
        
        # Otherwise, print the friendly user output
        print("\n" + "="*20)
        print("✨ Generated Commit Message:")
        print(commit_message)
        print("="*20 + "\n")
        print("If you like it, run this command:")
        print(f"git commit -m \"{commit_message}\"")
    elif not is_hook_mode:
        print("✅ No staged changes found. Nothing to commit.")