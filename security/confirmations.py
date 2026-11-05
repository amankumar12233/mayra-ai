"""Fail-closed confirmation policy for local computer changes."""

HIGH_IMPACT_CONFIRMATIONS = {
    "lock": "LOCK MY COMPUTER",
    "sleep": "SLEEP MY COMPUTER",
    "shutdown": "SHUT DOWN MY COMPUTER",
    "restart": "RESTART MY COMPUTER",
}


def required_confirmation(action, args):
    if action == "close_app":
        return "CLOSE APP", "Send a normal close request to the selected app. Save your work first."
    if action == "system_action":
        name = args.get("action")
        phrase = HIGH_IMPACT_CONFIRMATIONS.get(name)
        if phrase:
            return phrase, f"Aaru will {name} this computer. Save your work first."
    if action == "move_file":
        return "MOVE FILE", "Move the selected file inside Aaru AI Files."
    if action == "create_folder":
        return "CREATE FOLDER", "Create a folder inside Aaru AI Files."
    if action == "summarize_file":
        return "SEND FILE", "The selected text file will be sent to the configured AI provider."
    return None


def ask_for_confirmation(callback, action, args):
    request = required_confirmation(action, args)
    if request is None:
        return True
    phrase, description = request
    if callback is None:
        return False
    return callback(description, phrase) is True
